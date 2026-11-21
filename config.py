"""
Application settings for each environment.

Values come from the environment (.env), never from the code.
Choose the environment with APP_ENV=development | testing | production.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Settings shared by every environment."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY')

    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'medsync')

    LOG_LEVEL = 'INFO'
    LOG_FILE = os.getenv('LOG_FILE', 'logs/medsync.log')


class DevelopmentConfig(Config):
    """Local development: debug on, detailed logs."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SECRET_KEY = os.getenv('SECRET_KEY', 'development-only-key')


class TestingConfig(Config):
    """Automated tests: separate database, no log file."""
    TESTING = True
    LOG_LEVEL = 'WARNING'
    LOG_FILE = None
    SECRET_KEY = 'testing-only-key'
    MYSQL_DATABASE = os.getenv('MYSQL_TEST_DATABASE', 'medsync_test')


class ProductionConfig(Config):
    """Live deployment: debug off, SECRET_KEY must be set in the environment."""
    LOG_LEVEL = 'WARNING'


CONFIGS = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config(name=None):
    """Return the settings class for APP_ENV (default: development)."""
    name = (name or os.getenv('APP_ENV', 'development')).lower()
    if name not in CONFIGS:
        raise RuntimeError(f"APP_ENV must be one of: {', '.join(CONFIGS)}.")
    config = CONFIGS[name]
    if config is ProductionConfig and not config.SECRET_KEY:
        raise RuntimeError('SECRET_KEY must be set when APP_ENV=production.')
    return config