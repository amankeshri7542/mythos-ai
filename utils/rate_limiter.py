# utils/rate_limiter.py
import sqlite3
import hashlib
from datetime import datetime
import os

class RateLimiter:
    def __init__(self, db_path="data/rate_limits.db", max_videos_per_day=3):
        self.db_path = db_path
        self.max_videos = max_videos_per_day
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Create the database table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage (
                user_key TEXT PRIMARY KEY,
                count INTEGER NOT NULL,
                date TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user_key(self, identifier):
        """Generate a unique hash for the user"""
        today = datetime.now().date().isoformat()
        raw = f"{identifier}-{today}"
        return hashlib.sha256(raw.encode()).hexdigest()
    
    def check_limit(self, user_key):
        """
        Check if user has exceeded daily limit
        Returns: (can_proceed: bool, current_count: int, remaining: int)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        
        cursor.execute("SELECT count, date FROM usage WHERE user_key=?", (user_key,))
        result = cursor.fetchone()
        
        if result:
            count, stored_date = result
            
            if stored_date == today:
                # Same day - check limit
                remaining = self.max_videos - count
                can_proceed = count < self.max_videos
                conn.close()
                return can_proceed, count, remaining
            else:
                # New day - reset counter
                cursor.execute(
                    "UPDATE usage SET count=0, date=?, last_updated=CURRENT_TIMESTAMP WHERE user_key=?",
                    (today, user_key)
                )
                conn.commit()
                conn.close()
                return True, 0, self.max_videos
        else:
            # New user - create entry
            cursor.execute(
                "INSERT INTO usage (user_key, count, date) VALUES (?, 0, ?)",
                (user_key, today)
            )
            conn.commit()
            conn.close()
            return True, 0, self.max_videos
    
    def increment_usage(self, user_key):
        """Increment the usage count for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE usage SET count = count + 1, last_updated=CURRENT_TIMESTAMP WHERE user_key=?",
            (user_key,)
        )
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get usage statistics (for admin dashboard)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        
        cursor.execute("SELECT COUNT(*), SUM(count) FROM usage WHERE date=?", (today,))
        result = cursor.fetchone()
        
        conn.close()
        
        unique_users = result[0] if result[0] else 0
        total_videos = result[1] if result[1] else 0
        
        return {
            "unique_users_today": unique_users,
            "total_videos_today": total_videos
        }