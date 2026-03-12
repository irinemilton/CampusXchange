import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campus-barter-exchange-secret-key-2024'

    # MySQL Configuration
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'ROOT'
    MYSQL_HOST = 'localhost'
    MYSQL_DB = 'campus_barter'

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
