import sqlite3
from datetime import datetime

class SchedulerDatabase:
    def __init__(self, db_name: str = "bot_scheduler.db"):
        self.database_name = db_name
        self.create_tables()

    def get_connection(self):
        connection = sqlite3.connect(self.database_name)
        return connection

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    post_text TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    is_published INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def add_scheduled_post(self, channel_id: str, post_text: str, scheduled_time: datetime) -> int:
        time_string = scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scheduled_posts (channel_id, post_text, scheduled_time)
                VALUES (?, ?, ?)
            ''', (channel_id, post_text, time_string))
            conn.commit()
            return cursor.lastrowid

    def get_pending_posts(self) -> list:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT post_id, channel_id, post_text 
                FROM scheduled_posts 
                WHERE is_published = 0 AND scheduled_time <= ?
            ''', (current_time_str,))
            return cursor.fetchall()

    def mark_post_as_published(self, post_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scheduled_posts 
                SET is_published = 1 
                WHERE post_id = ?
            ''', (post_id,))
            conn.commit()
          
