from flask import Flask, render_template, request, jsonify

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a real secret in production!


# Route: Home/Dashboard
@app.route('/')
def index():
    """Display the inventory dashboard"""
    return render_template('index.html')


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

