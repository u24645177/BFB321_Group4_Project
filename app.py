from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

from data import dashboard

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a real secret in production!


# Route: Home/Dashboard
@app.route('/')
def index():
    """Display the inventory dashboard"""
    return render_template('index.html', **dashboard.get_dashboard_context())


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


# Route: Handle form submission (optional for now)
@app.route('/add-medicine', methods=['POST'])
def add_medicine():
    """Handle adding a new medicine"""
    data = request.form
    # For now, just return success (we'll connect the database later in Step 3)
    return jsonify({'success': True, 'message': 'Medicine added successfully!'})


# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5001)

