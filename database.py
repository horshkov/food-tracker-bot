import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
        self.ensure_tables()

    def ensure_tables(self):
        with self.conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT
                );
                CREATE TABLE IF NOT EXISTS food_entries (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(id),
                    description TEXT,
                    calories FLOAT,
                    protein FLOAT,
                    carbs FLOAT,
                    fats FLOAT,
                    analysis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self.conn.commit()

    def add_user(self, user_id, username, first_name, last_name):
        with self.conn.cursor() as cur:
            cur.execute('''
                INSERT INTO users (id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET username=EXCLUDED.username, first_name=EXCLUDED.first_name, last_name=EXCLUDED.last_name;
            ''', (user_id, username, first_name, last_name))
            self.conn.commit()

    def add_food_entry(self, user_id, result):
        with self.conn.cursor() as cur:
            cur.execute('''
                INSERT INTO food_entries (user_id, description, calories, protein, carbs, fats, analysis)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                result.get("description", ""),
                float(result.get("calories", 0)),
                float(result.get("protein", 0)),
                float(result.get("carbs", 0)),
                float(result.get("fats", 0)),
                result.get("analysis", "")
            ))
            self.conn.commit()

    def get_user_stats(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute('''
                SELECT COUNT(*) AS total_entries,
                       COALESCE(SUM(calories),0) AS total_calories,
                       COALESCE(SUM(protein),0) AS total_protein,
                       COALESCE(SUM(carbs),0) AS total_carbs,
                       COALESCE(SUM(fats),0) AS total_fats,
                       COALESCE(AVG(calories),0) AS avg_calories,
                       COALESCE(AVG(protein),0) AS avg_protein,
                       COALESCE(AVG(carbs),0) AS avg_carbs,
                       COALESCE(AVG(fats),0) AS avg_fats
                FROM food_entries WHERE user_id = %s
            ''', (user_id,))
            return cur.fetchone()

    def get_user_history(self, user_id, limit=10):
        with self.conn.cursor() as cur:
            cur.execute('''
                SELECT * FROM food_entries WHERE user_id = %s ORDER BY created_at DESC LIMIT %s
            ''', (user_id, limit))
            return cur.fetchall()

    def get_entry(self, user_id, entry_id):
        with self.conn.cursor() as cur:
            cur.execute('''
                SELECT * FROM food_entries WHERE user_id = %s AND id = %s
            ''', (user_id, entry_id))
            return cur.fetchone()

    def delete_entry(self, user_id, entry_id):
        with self.conn.cursor() as cur:
            cur.execute('''
                DELETE FROM food_entries WHERE user_id = %s AND id = %s
            ''', (user_id, entry_id))
            deleted = cur.rowcount
            self.conn.commit()
            return deleted > 0 