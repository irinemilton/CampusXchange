import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campus-barter-exchange-secret-key-2024'
    
    # MySQL Configuration - Update these for your MySQL setup
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'campus_barter'
    
    # Use MySQL if available, otherwise fallback to SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class SQLiteConfig(Config):
    """Fallback SQLite config for development without MySQL"""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'campus_barter.db')
