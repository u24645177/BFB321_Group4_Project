from flask import Flask

from config import get_config
from errors import register_error_handlers
from logging_setup import setup_logging
from routes.pages import pages_bp
from routes.api import api_bp
import db

# Create Flask app and load settings for the current environment (config.py)
app = Flask(__name__)
app.config.from_object(get_config())

# Logging and central error handlers (logging_setup.py, errors.py)
setup_logging(app)
register_error_handlers(app)

# Open and close a MySQL connection per request (db.py)
db.init_app(app)

# Register blueprints
#   pages_bp -> HTML pages (/, /reorder, /tracking, /kpis)
#   api_bp   -> JSON endpoints (all start with /api)
app.register_blueprint(pages_bp)
app.register_blueprint(api_bp)


# Run the app
if __name__ == '__main__':
        app.run(debug=app.config['DEBUG'], host='localhost', port=5001)
    