import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = "food_tracker.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create food_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS food_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    description TEXT,
                    calories INTEGER,
                    protein REAL,
                    carbs REAL,
                    fats REAL,
                    analysis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()

    def add_user(self, user_id: int, username: Optional[str] = None, 
                first_name: Optional[str] = None, last_name: Optional[str] = None) -> None:
        """Add a new user or update existing user information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()

    def add_food_entry(self, user_id: int, food_data: Dict[str, Any]) -> None:
        """Add a new food entry to the user's history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO food_history 
                (user_id, description, calories, protein, carbs, fats, analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                food_data.get('description', ''),
                food_data.get('calories', 0),
                food_data.get('protein', 0.0),
                food_data.get('carbs', 0.0),
                food_data.get('fats', 0.0),
                food_data.get('analysis', '')
            ))
            conn.commit()

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's food history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, description, calories, protein, carbs, fats, analysis, created_at
                FROM food_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            columns = ['id', 'description', 'calories', 'protein', 'carbs', 'fats', 'analysis', 'created_at']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's nutritional statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_entries,
                    AVG(calories) as avg_calories,
                    AVG(protein) as avg_protein,
                    AVG(carbs) as avg_carbs,
                    AVG(fats) as avg_fats,
                    SUM(calories) as total_calories,
                    SUM(protein) as total_protein,
                    SUM(carbs) as total_carbs,
                    SUM(fats) as total_fats
                FROM food_history
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            return {
                'total_entries': row[0],
                'avg_calories': round(row[1] or 0),
                'avg_protein': round(row[2] or 0, 1),
                'avg_carbs': round(row[3] or 0, 1),
                'avg_fats': round(row[4] or 0, 1),
                'total_calories': round(row[5] or 0),
                'total_protein': round(row[6] or 0, 1),
                'total_carbs': round(row[7] or 0, 1),
                'total_fats': round(row[8] or 0, 1)
            }

    def delete_entry(self, user_id: int, entry_id: int) -> bool:
        """Delete a specific food entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM food_history
                    WHERE id = ? AND user_id = ?
                ''', (entry_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting entry: {str(e)}")
            return False

    def get_entry(self, user_id: int, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific food entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, description, calories, protein, carbs, fats, analysis, created_at
                FROM food_history
                WHERE id = ? AND user_id = ?
            ''', (entry_id, user_id))
            
            row = cursor.fetchone()
            if row:
                columns = ['id', 'description', 'calories', 'protein', 'carbs', 'fats', 'analysis', 'created_at']
                return dict(zip(columns, row))
            return None 