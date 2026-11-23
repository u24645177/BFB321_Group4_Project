"""
Shared test setup. Runs before any test file is imported.

APP_ENV=testing makes config.py use TestingConfig (separate database name,
no log file), so running the tests never touches the development setup.
"""

import os

os.environ['APP_ENV'] = 'testing'
