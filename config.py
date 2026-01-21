import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'katapayadi-microproject-2024-dev-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///katapayadi.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False