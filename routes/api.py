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


# Route: EOQ order recommendation for one medicine (Flow 2)
@api_bp.route('/eoq', methods=['GET'])
def eoq_recommendation():
    """
    Recommend an order quantity using the EOQ model.

    Request:  GET /api/eoq?medicine=Paracetamol 500mg
    Response: 200 {"data": {"medicine", "recommended_quantity", "annual_demand", "order_cost",
                            "holding_cost", "current_stock", "reorder_point", "status"}}
              400 when ?medicine= is missing, 404 when the medicine does not exist
    """
    name = request.args.get('medicine', '').strip()
    if not name:
        return jsonify({'error': 'Add ?medicine= to the URL.'}), 400

    recommendation = dashboard.recommend_order(name)
    if recommendation is None:
        return jsonify({'error': f'{name} was not found.'}), 404
    return jsonify({'data': recommendation}), 200


# Route: Create a reorder request (Flow 2)
@api_bp.route('/requests', methods=['POST'])
def create_request():
    """
    Create a reorder request. It always starts as Awaiting Approval.

    Request:  {"medicine": "Paracetamol 500mg", "quantity": 418, "supplier": "MediSupply SA",
               "expected_delivery": "2026-12-01", "priority": "Routine", "notes": ""}
    Response: 201 {"data": {"id", "medicine", "quantity", "supplier", "status", "status_class",
                            "request_date", "expected_delivery", "emergency", "notes",
                            "next_status", "next_action"}}
              400 {"error": "...", "fields": {"field_name": "message"}} when input is invalid
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'error': 'Send the request as JSON.'}), 400

    # Reuse the same validation as the dashboard order form
    order, errors = dashboard.validate_order({key: str(value) for key, value in payload.items()})
    if errors:
        return jsonify({'error': 'Please fix the highlighted fields.', 'fields': errors}), 400

    new_request = dashboard.add_request(order, emergency=payload.get('priority') == 'Emergency')
    return jsonify({'data': dashboard.request_to_json(new_request)}), 201


# Route: Move a request to its next status (Flow 2)
@api_bp.route('/requests/<int:request_id>/status', methods=['PATCH'])
def advance_request_status(request_id):
    """
    Move a request one step: Awaiting Approval -> Approved -> Ordered -> In Transit -> Delivered.
    Delivering adds the quantity to the medicine's stock.

    Response: 200 {"data": {"request": {...}, "inventory": {"name", "current_stock",
                            "reorder_point", "safety_stock", "status"}}}
              404 when the request does not exist, 409 when it is already delivered
    """
    updated, error = dashboard.advance_request(request_id)
    if error:
        status_code = 404 if 'not found' in error else 409
        return jsonify({'error': error}), status_code

    return jsonify({'data': {
        'request': dashboard.request_to_json(updated),
        'inventory': dashboard.inventory_row(updated['medicine']),
    }}), 200