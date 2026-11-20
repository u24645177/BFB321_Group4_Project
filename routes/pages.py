"""
Page routes: every route here returns an HTML page (render_template) or redirects back to one after a form is submitted.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from data import dashboard
from data.deliveries import DELIVERIES, FACILITIES, delivery_summary

pages_bp = Blueprint('pages', __name__)


# Route: Home/Dashboard
@pages_bp.route('/')
def index():
    """Display the inventory dashboard, filtered by selected medicine category"""
    category = request.args.get('category', 'all')
    return render_template('index.html', **dashboard.get_dashboard_context(category))


# Route: Place a new reorder request from the dashboard form
@pages_bp.route('/orders', methods=['POST'])
def place_order():
    """Validate the order form and add it as an Awaiting Approval request"""
    order, errors = dashboard.validate_order(request.form)
    if errors:
        # Re-render with the submitted values so the user can fix the errors
        return render_template('index.html', **dashboard.get_dashboard_context(),
                               form_errors=errors, form_values=request.form), 400

    dashboard.add_request(order)
    flash(f"Order for {order['quantity']:,} × {order['medicine']} submitted. Status: Awaiting Approval.", 'success')
    return redirect(url_for('pages.index', _anchor='requests'))


# Route: Handle form submission
@pages_bp.route('/add-medicine', methods=['POST'])
def add_medicine():
    """Handle adding a new medicine"""
    data = request.form
    # For now, just confirm (we'll connect the database later in Step 3)
    flash(f"{data.get('medicine_name')} added successfully.", 'success')
    return redirect(url_for('pages.index'))


# Route: Reorder request form
@pages_bp.route('/reorder', methods=['GET', 'POST'])
def reorder():
    """Display and handle the reorder request form"""
    if request.method == 'POST':
        data = request.form
        flash(f"Reorder request for {data.get('quantity')} units of "
              f"{data.get('medicine')} submitted.", 'success')
        return redirect(url_for('pages.reorder'))
    return render_template('reorder.html', medicines=dashboard.build_inventory(), facilities=FACILITIES, suppliers=dashboard.SUPPLIERS)


# Route: Order tracking / delivery board
@pages_bp.route('/tracking')
def tracking():
    """Display the logistics delivery board"""
    return render_template('tracking.html', deliveries=DELIVERIES, summary=delivery_summary())


# Route: Update a delivery exception (from the modal)
@pages_bp.route('/tracking/<delivery_id>/exception', methods=['POST'])
def update_exception(delivery_id):
    """Record a delivery exception"""
    for delivery in DELIVERIES:
        if delivery['id'] == delivery_id:
            delivery['status'] = request.form.get('status', delivery['status'])
            delivery['exception'] = request.form.get('exception', '')
            flash(f"Delivery {delivery_id} updated.", 'success')
            break
    else:
        flash(f"Delivery {delivery_id} not found.", 'danger')
    return redirect(url_for('pages.tracking'))

# Route: KPI dashboard
@pages_bp.route('/kpis')
def kpis():
    """Display the KPI dashboard"""
    context = dashboard.get_dashboard_context()
    return render_template('kpis.html', kpis=context['metrics'], medicines=context['inventory'], deliveries=DELIVERIES, summary=delivery_summary())