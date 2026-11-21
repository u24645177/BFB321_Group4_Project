from flask import Flask

from routes.pages import pages_bp
from routes.api import api_bp
import db

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a real secret in production!

# Open and close a MySQL connection per request (db.py)
db.init_app(app)

# Register blueprints
#   pages_bp -> HTML pages (/, /reorder, /tracking, /kpis)
#   api_bp   -> JSON endpoints (all start with /api)
app.register_blueprint(pages_bp)
app.register_blueprint(api_bp)


# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5001)
    