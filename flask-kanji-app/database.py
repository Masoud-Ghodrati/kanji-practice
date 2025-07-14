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
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (username, character, direction),
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
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

def save_progress(username, character, direction, correct):
    with get_db() as conn:
        conn.execute('INSERT OR REPLACE INTO progress (username, character, direction, correct) VALUES (?, ?, ?, ?)', 
                    (username, character, direction, correct))
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

def get_user_stats(username):
    with get_db() as conn:
        # Overall stats
        total = conn.execute('SELECT COUNT(*) as count FROM progress WHERE username = ?', 
                           (username,)).fetchone()['count']
        correct = conn.execute('SELECT COUNT(*) as count FROM progress WHERE username = ? AND correct = 1', 
                             (username,)).fetchone()['count']
        
        # Direction breakdown
        jp_to_en = conn.execute('SELECT COUNT(*) as total, SUM(correct) as correct FROM progress WHERE username = ? AND direction = ?', 
                               (username, 'Japanese → English')).fetchone()
        en_to_jp = conn.execute('SELECT COUNT(*) as total, SUM(correct) as correct FROM progress WHERE username = ? AND direction = ?', 
                               (username, 'English → Japanese')).fetchone()
        
        # Recent progress (last 7 days)
        recent = conn.execute('''SELECT DATE(answered_at) as date, COUNT(*) as total, SUM(correct) as correct 
                                FROM progress WHERE username = ? AND answered_at >= date('now', '-7 days') 
                                GROUP BY DATE(answered_at) ORDER BY date''', 
                             (username,)).fetchall()
        
        return {
            'total_answered': total,
            'total_correct': correct or 0,
            'overall_percentage': round((correct or 0) / total * 100, 1) if total > 0 else 0,
            'jp_to_en': {
                'total': jp_to_en['total'] or 0,
                'correct': jp_to_en['correct'] or 0,
                'percentage': round((jp_to_en['correct'] or 0) / jp_to_en['total'] * 100, 1) if jp_to_en['total'] > 0 else 0
            },
            'en_to_jp': {
                'total': en_to_jp['total'] or 0,
                'correct': en_to_jp['correct'] or 0,
                'percentage': round((en_to_jp['correct'] or 0) / en_to_jp['total'] * 100, 1) if en_to_jp['total'] > 0 else 0
            },
            'recent_progress': [{
                'date': row['date'],
                'total': row['total'],
                'correct': row['correct'] or 0,
                'percentage': round((row['correct'] or 0) / row['total'] * 100, 1)
            } for row in recent]
        }