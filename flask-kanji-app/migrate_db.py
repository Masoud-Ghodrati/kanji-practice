import sqlite3

DATABASE = 'kanji.db'

def migrate_database():
    with sqlite3.connect(DATABASE) as conn:
        # Check if columns exist
        cursor = conn.execute("PRAGMA table_info(progress)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'answer_time_ms' not in columns:
            print("Adding answer_time_ms column...")
            conn.execute('ALTER TABLE progress ADD COLUMN answer_time_ms INTEGER DEFAULT 0')
        
        if 'session_id' not in columns:
            print("Adding session_id column...")
            conn.execute('ALTER TABLE progress ADD COLUMN session_id TEXT')
        
        conn.commit()
        print("Database migration completed!")

if __name__ == '__main__':
    migrate_database()