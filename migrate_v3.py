
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

# Add Bio to student table
try:
    cursor.execute("ALTER TABLE student ADD COLUMN Bio TEXT NULL")
    print("SUCCESS: Bio column added to student table.")
except Exception as e:
    if "Duplicate column name" in str(e):
        print("INFO: student.Bio column already exists.")
    else:
        print(f"Error: {e}")

# Add ViewCount to item table
try:
    cursor.execute("ALTER TABLE item ADD COLUMN ViewCount INT DEFAULT 0")
    print("SUCCESS: ViewCount column added to item table.")
except Exception as e:
    if "Duplicate column name" in str(e):
        print("INFO: item.ViewCount column already exists.")
    else:
        print(f"Error: {e}")

conn.commit()
cursor.close()
conn.close()
