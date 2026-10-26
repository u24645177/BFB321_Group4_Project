from flask import Flask, render_template, request, redirect, url_for, flash

from data import dashboard

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a real secret in production!

# ---------------------------------------------------------------------------
   # Sample data (placeholder until the MySQL database is connected in Step 3).
   # Medicines, KPIs and reorder requests live in data/dashboard.py.
# ---------------------------------------------------------------------------

FACILITIES = ['Steve Biko Academic Hospital', 'Kalafong Hospital', 'Tshwane District Hospital']

DELIVERIES = [
    {'id': 'DEL-1042', 'route': 'Depot → Steve Biko Academic', 'vehicle': 'GP 12-34 AB',
     'eta': '2026-10-21 09:30', 'status': 'In Transit', 'exception': ''},
    {'id': 'DEL-1043', 'route': 'Depot → Kalafong', 'vehicle': 'GP 56-78 CD',
     'eta': '2026-10-20 14:00', 'status': 'Delayed', 'exception': 'Vehicle breakdown on N4'},
    {'id': 'DEL-1044', 'route': 'Depot → Tshwane District', 'vehicle': 'GP 90-12 EF',
     'eta': '2026-10-19 11:15', 'status': 'Delivered', 'exception': ''},
    {'id': 'DEL-1045', 'route': 'Depot → Steve Biko Academic', 'vehicle': 'GP 34-56 GH',
     'eta': '2026-10-22 08:00', 'status': 'Scheduled', 'exception': ''},
]

# Route: Home/Dashboard
@app.route('/')
def index():
    """Display the inventory dashboard, filtered by selected medicine category"""
    category = request.args.get('category', 'all')
    return render_template('index.html', **dashboard.get_dashboard_context(category))


# Route: Place a new reorder request from the dashboard form
@app.route('/orders', methods=['POST'])
def place_order():
    """Validate the order form and add it as an Awaiting Approval request"""
    order, errors = dashboard.validate_order(request.form)
    if errors:
        # Re-render with the submitted values so the user can fix the errors
        return render_template('index.html', **dashboard.get_dashboard_context(),
                               form_errors=errors, form_values=request.form), 400

    dashboard.add_request(order)
    flash(f"Order for {order['quantity']:,} × {order['medicine']} submitted. Status: Awaiting Approval.", 'success')
    return redirect(url_for('index', _anchor='requests'))


# Route: Handle form submission
@app.route('/add-medicine', methods=['POST'])
def add_medicine():
    """Handle adding a new medicine"""
    data = request.form
    # For now, just confirm (we'll connect the database later in Step 3)
    flash(f"{data.get('medicine_name')} added successfully.", 'success')
    return redirect(url_for('index'))


# Route: Reorder request form
@app.route('/reorder', methods=['GET', 'POST'])
def reorder():
    """Display and handle the reorder request form"""
    if request.method == 'POST':
        data = request.form
        flash(f"Reorder request for {data.get('quantity')} units of "
              f"{data.get('medicine')} submitted.", 'success')
        return redirect(url_for('reorder'))
    return render_template('reorder.html', medicines=dashboard.build_inventory(), facilities=FACILITIES)


# Route: Order tracking / delivery board
@app.route('/tracking')
def tracking():
    """Display the logistics delivery board"""
    return render_template('tracking.html', deliveries=DELIVERIES)


# Route: Update a delivery exception (from the modal)
@app.route('/tracking/<delivery_id>/exception', methods=['POST'])
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
    return redirect(url_for('tracking'))


# Route: KPI dashboard
@app.route('/kpis')
def kpis():
    """Display the KPI dashboard"""
    context = dashboard.get_dashboard_context()
    return render_template('kpis.html', kpis=context['metrics'], medicines=context['inventory'], deliveries=DELIVERIES)


# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5001)
