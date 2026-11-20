"""
API routes: every route here returns JSON, never HTML.
All URLs in this file automatically start with /api (set by url_prefix when the blueprint is registered in app.py).
Endpoints for medicines, requests, deliveries and KPIs get added here.
"""

from flask import Blueprint, jsonify, request

from data import dashboard


api_bp = Blueprint('api', __name__, url_prefix='/api')


# Route: Health check - confirms the API blueprint is registered and running
@api_bp.route('/health', methods=['GET'])
def health():
    """Return a simple status message"""
    return jsonify({'status': 'ok'}), 200


# Route: Add a new medicine (Flow 1)
@api_bp.route('/medicines', methods=['POST'])
def create_medicine():
    """
    Create a medicine from a JSON body.

    Request:  {"name": "Aspirin 300mg", "category": "analgesics", "current_stock": 120,
               "avg_daily_demand": 8, "demand_std_dev": 2, "lead_time_days": 7}
    Response: 201 {"data": {"name", "category", "current_stock", "reorder_point", "safety_stock", "status"}}
              400 {"error": "...", "fields": {"field_name": "message"}} when input is invalid
              409 {"error": "..."} when the medicine already exists
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'Send the medicine as JSON.'}), 400

    medicine, errors = dashboard.validate_medicine(payload)
    if errors:
        return jsonify({'error': 'Please fix the highlighted fields.', 'fields': errors}), 400

    if dashboard.medicine_exists(medicine['name']):
        return jsonify({'error': f"{medicine['name']} is already in the inventory.",
                        'fields': {'name': 'This medicine already exists.'}}), 409

    row = dashboard.add_medicine(medicine)
    return jsonify({'data': row}), 201

