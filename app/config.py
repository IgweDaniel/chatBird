import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    MAIL_PORT = 587
    MAIL_SERVER = 'smtp.googlemail.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    MAIL_USERNAME = os.getenv("EMAIL")
    MAIL_DEFAULT_SENDER = os.getenv("EMAIL")
    MAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{os.getenv("DB_USER")}:{os.getenv("DB_PW")}@localhost:5432/chatbird'
    MAIL_USE_TLS = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{os.getenv("DB_USER")}:{os.getenv("DB_PW")}@localhost:5432/chatbird'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{os.getenv("DB_USER")}:{os.getenv("DB_PW")}@localhost:5432/postgres'
