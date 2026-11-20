"""
API routes: every route here returns JSON, never HTML.
All URLs in this file automatically start with /api (set by url_prefix when the blueprint is registered in app.py).
Endpoints for medicines, requests, deliveries and KPIs get added here.
"""

from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__, url_prefix='/api')


# Route: Health check - confirms the API blueprint is registered and running
@api_bp.route('/health', methods=['GET'])
def health():
    """Return a simple status message"""
    return jsonify({'status': 'ok'}), 200
