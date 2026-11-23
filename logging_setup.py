"""
Logging: levelled messages to the console and to a rotating log file.
Every message records the time, level, module and text.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FORMAT = '%(asctime)s %(levelname)s [%(name)s] %(message)s'


def setup_logging(app):
    """Configure console and file logging using the app's LOG_LEVEL and LOG_FILE."""
    if app.extensions.get('logging_configured'):
        return  # avoid duplicate handlers when the debug reloader restarts

    level = getattr(logging, str(app.config.get('LOG_LEVEL', 'INFO')).upper(), logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)

    root = logging.getLogger()
    root.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    log_file = app.config.get('LOG_FILE')
    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    app.extensions['logging_configured'] = True