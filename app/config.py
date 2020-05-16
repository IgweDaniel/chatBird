import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        basedir, 'database.db')

    DATABASE_URI = 'sqlite:///:memory:'
    MAIL_PORT = 587
    MAIL_SERVER = 'smtp.googlemail.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    MAIL_USERNAME = os.getenv("EMAIL")
    MAIL_DEFAULT_SENDER = os.getenv("EMAIL")
    MAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


class ProductionConfig(Config):
    DATABASE_URI = 'mysql://user@localhost/foo'
    MAIL_USE_TLS = True


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
