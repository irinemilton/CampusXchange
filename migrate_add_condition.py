"""
Migration: Add Condition column to item table
Run once: python migrate_add_condition.py
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
        "ALTER TABLE item ADD COLUMN `Condition` ENUM('New','Like New','Good','Fair') DEFAULT 'Good'"
    )
    conn.commit()
    print("SUCCESS: Condition column added to item table.")
except Exception as e:
    if "Duplicate column name" in str(e):
        print("Column already exists, skipping.")
    else:
        print(f"Error: {e}")
finally:
    cursor.close()
    conn.close()
