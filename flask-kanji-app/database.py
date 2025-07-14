import sqlite3
import bcrypt
import json
from contextlib import contextmanager

DATABASE = 'kanji.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                username TEXT PRIMARY KEY,
                num_chars INTEGER DEFAULT 2200,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                username TEXT,
                character TEXT,
                direction TEXT,
                correct INTEGER,
                answer_time_ms INTEGER DEFAULT 0,
                session_id TEXT,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (username, character, direction),
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # Add missing columns if they don't exist
        try:
            conn.execute('ALTER TABLE progress ADD COLUMN answer_time_ms INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            conn.execute('ALTER TABLE progress ADD COLUMN session_id TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(username, password):
    with get_db() as conn:
        try:
            password_hash = hash_password(password)
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                        (username, password_hash))
            conn.execute('INSERT INTO user_settings (username) VALUES (?)', (username,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def authenticate_user(username, password):
    with get_db() as conn:
        user = conn.execute('SELECT password_hash FROM users WHERE username = ?', 
                           (username,)).fetchone()
        if user and verify_password(password, user['password_hash']):
            return True
    return False

def get_user_settings(username):
    with get_db() as conn:
        settings = conn.execute('SELECT num_chars FROM user_settings WHERE username = ?', 
                               (username,)).fetchone()
        return settings['num_chars'] if settings else 2200

def save_user_settings(username, num_chars):
    with get_db() as conn:
        conn.execute('INSERT OR REPLACE INTO user_settings (username, num_chars) VALUES (?, ?)', 
                    (username, num_chars))
        conn.commit()

def get_progress(username, direction):
    with get_db() as conn:
        rows = conn.execute('SELECT character, correct FROM progress WHERE username = ? AND direction = ?', 
                           (username, direction)).fetchall()
        return {row['character']: row['correct'] for row in rows}

def save_progress(username, character, direction, correct, answer_time_ms=0, session_id=None):
    with get_db() as conn:
        conn.execute('INSERT OR REPLACE INTO progress (username, character, direction, correct, answer_time_ms, session_id) VALUES (?, ?, ?, ?, ?, ?)', 
                    (username, character, direction, correct, answer_time_ms, session_id))
        conn.commit()

def delete_progress_item(username, character, direction):
    with get_db() as conn:
        conn.execute('DELETE FROM progress WHERE username = ? AND character = ? AND direction = ?', 
                    (username, character, direction))
        conn.commit()

def reset_progress(username, direction):
    with get_db() as conn:
        conn.execute('DELETE FROM progress WHERE username = ? AND direction = ?', 
                    (username, direction))
        conn.commit()

def get_user_stats(username, direction=None, session_id=None):
    with get_db() as conn:
        where_clause = 'WHERE username = ?'
        params = [username]
        
        if direction:
            where_clause += ' AND direction = ?'
            params.append(direction)
        
        if session_id:
            where_clause += ' AND session_id = ?'
            params.append(session_id)
        
        # Overall stats
        total = conn.execute(f'SELECT COUNT(*) as count FROM progress {where_clause}', params).fetchone()['count']
        correct = conn.execute(f'SELECT COUNT(*) as count FROM progress {where_clause} AND correct = 1', params).fetchone()['count']
        
        # Timing stats
        timing = conn.execute(f'''SELECT 
            AVG(CASE WHEN correct = 1 THEN answer_time_ms END) as avg_correct_time,
            AVG(CASE WHEN correct = 0 THEN answer_time_ms END) as avg_incorrect_time,
            MIN(answer_time_ms) as fastest_time,
            MAX(answer_time_ms) as slowest_time
            FROM progress {where_clause} AND answer_time_ms > 0''', params).fetchone()
        
        # Direction breakdown (only if no direction filter)
        direction_stats = {}
        if not direction:
            for dir_name in ['Japanese → English', 'English → Japanese']:
                dir_params = [username, dir_name]
                if session_id:
                    dir_params.append(session_id)
                    dir_where = 'WHERE username = ? AND direction = ? AND session_id = ?'
                else:
                    dir_where = 'WHERE username = ? AND direction = ?'
                
                dir_data = conn.execute(f'SELECT COUNT(*) as total, SUM(correct) as correct FROM progress {dir_where}', dir_params).fetchone()
                direction_stats[dir_name.replace(' → ', '_to_').replace('Japanese', 'jp').replace('English', 'en')] = {
                    'total': dir_data['total'] or 0,
                    'correct': dir_data['correct'] or 0,
                    'percentage': round((dir_data['correct'] or 0) / dir_data['total'] * 100, 1) if dir_data['total'] > 0 else 0
                }
        
        # Recent progress (last 7 days)
        recent = conn.execute(f'''SELECT DATE(answered_at) as date, COUNT(*) as total, SUM(correct) as correct,
                                AVG(CASE WHEN correct = 1 THEN answer_time_ms END) as avg_correct_time,
                                AVG(CASE WHEN correct = 0 THEN answer_time_ms END) as avg_incorrect_time
                                FROM progress {where_clause} AND answered_at >= date('now', '-7 days') 
                                GROUP BY DATE(answered_at) ORDER BY date''', params).fetchall()
        
        return {
            'total_answered': total,
            'total_correct': correct or 0,
            'overall_percentage': round((correct or 0) / total * 100, 1) if total > 0 else 0,
            'avg_correct_time': round(timing['avg_correct_time'] or 0),
            'avg_incorrect_time': round(timing['avg_incorrect_time'] or 0),
            'fastest_time': timing['fastest_time'] or 0,
            'slowest_time': timing['slowest_time'] or 0,
            **direction_stats,
            'recent_progress': [{
                'date': row['date'],
                'total': row['total'],
                'correct': row['correct'] or 0,
                'percentage': round((row['correct'] or 0) / row['total'] * 100, 1),
                'avg_correct_time': round(row['avg_correct_time'] or 0),
                'avg_incorrect_time': round(row['avg_incorrect_time'] or 0)
            } for row in recent]
        }

def get_current_session_id(username):
    with get_db() as conn:
        result = conn.execute('SELECT session_id FROM progress WHERE username = ? ORDER BY answered_at DESC LIMIT 1', (username,)).fetchone()
        return result['session_id'] if result else None