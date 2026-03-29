"""
Migration: Add DateListed column to item table
Run once: python migrate_add_datelisted.py
"""
import pymysql
from config import Config

cfg = Config()

conn = pymysql.connect(
    host=cfg.MYSQL_HOST,
    user=cfg.MYSQL_USER,
    password=cfg.MYSQL_PASSWORD,
    database=cfg.MYSQL_DB
)
cursor = conn.cursor()

try:
    cursor.execute(
        "ALTER TABLE item ADD COLUMN DateListed DATETIME DEFAULT CURRENT_TIMESTAMP"
    )
    conn.commit()
    print("SUCCESS: DateListed column added to item table.")
except Exception as e:
    if "Duplicate column name" in str(e):
        print("Column already exists, skipping.")
    else:
        print(f"Error: {e}")
finally:
    cursor.close()
    conn.close()
