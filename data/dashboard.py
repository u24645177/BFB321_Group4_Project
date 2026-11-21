"""
Dashboard Data: KPIs, reorder requests, alerts and inventory for the dashboard.

This is placeholder data until the database is connected (Step 3). The route
only calls get_dashboard_context(), validate_order() and add_request(), so the
lists below can later be swapped for database queries without touching the
template.

Only the raw records are typed in. Everything the dashboard shows as a status
(KPI colour, trend, inventory level, days in status, alerts) is derived from
them, so the page always agrees with itself:
    - Reorder points and safety stock come from models/eoq.py.
    - Inventory is Critical below safety stock, Low at or below the reorder point.
    - Alerts are generated from critical KPIs, delayed or overdue orders and
      requests waiting longer than the approval SLA.
"""

import math
from datetime import date, timedelta

from models.eoq import calculate_eoq, calculate_reorder_point, calculate_safety_stock

SERVICE_LEVEL_Z = 1.65      # 95% service level
APPROVAL_SLA_DAYS = 2       # requests waiting longer than this are a bottleneck
MAX_ORDER_QUANTITY = 100_000
MAX_NOTES_LENGTH = 500

# Display status -> CSS modifier used by the template's badges
REQUEST_STATUSES = {
    'Awaiting Approval': 'awaiting',
    'Approved': 'approved',
    'Ordered': 'ordered',
    'In Transit': 'transit',
    'Delivered': 'delivered',
    'Delayed': 'delayed',
}
OPEN_STATUSES = ('Approved', 'Ordered', 'In Transit')

SUPPLIERS = [
    'MediSupply SA',
    'PharmaLink Distributors',
    'HealthCore Wholesale',
    'Afrimed Logistics',
]

# Demand statistics and supplier lead time drive each medicine's reorder point
MEDICINES = [
    {'name': 'Paracetamol 500mg', 'category': 'analgesics', 'current_stock': 95, 'avg_daily_demand': 12, 'demand_std_dev': 4, 'lead_time_days': 7},
    {'name': 'Amoxicillin 250mg', 'category': 'antibiotics', 'current_stock': 140, 'avg_daily_demand': 6, 'demand_std_dev': 2, 'lead_time_days': 10},
    {'name': 'Ibuprofen 400mg', 'category': 'analgesics', 'current_stock': 9, 'avg_daily_demand': 10, 'demand_std_dev': 3, 'lead_time_days': 7},
    {'name': 'Metformin 500mg', 'category': 'antidiabetics', 'current_stock': 260, 'avg_daily_demand': 8, 'demand_std_dev': 2, 'lead_time_days': 14},
    {'name': 'Insulin Glargine 100U/ml', 'category': 'antidiabetics', 'current_stock': 6, 'avg_daily_demand': 3, 'demand_std_dev': 1, 'lead_time_days': 21},
    {'name': 'Salbutamol Inhaler', 'category': 'respiratory', 'current_stock': 58, 'avg_daily_demand': 5, 'demand_std_dev': 2, 'lead_time_days': 10},
    {'name': 'Tenofovir/Emtricitabine', 'category': 'antiretrovirals', 'current_stock': 210, 'avg_daily_demand': 7, 'demand_std_dev': 1.5, 'lead_time_days': 14},
]


# KPIs from the project proposal. Status thresholds:
#   goal 'decrease': value <= target is good, value <= limit is a warning, above is critical
#   goal 'increase': value >= target is good, value >= limit is a warning, below is critical
# scale_max sets the full width of the progress bar.
KPI_DEFINITIONS = [
    {'key': 'stockout_frequency', 'name': 'Medicine Stockout Frequency', 'goal': 'decrease',
     'value': 4, 'previous': 6, 'target': 1, 'limit': 3, 'unit': '/ month', 'decimals': 0, 'scale_max': 10,
     'description': 'Stockout events recorded this month.'},
    {'key': 'procurement_lead_time', 'name': 'Avg Procurement Lead Time', 'goal': 'decrease',
     'value': 9.5, 'previous': 11.2, 'target': 7, 'limit': 10, 'unit': 'days', 'decimals': 1, 'scale_max': 21,
     'description': 'From approved request to delivery.'},
    {'key': 'approval_time', 'name': 'Avg Approval Time', 'goal': 'decrease',
     'value': 30, 'previous': 26, 'target': 24, 'limit': 48, 'unit': 'hrs', 'decimals': 0, 'scale_max': 72,
     'description': 'From request submission to approval.'},
    {'key': 'record_accuracy', 'name': 'Inventory Record Accuracy', 'goal': 'increase',
     'value': 96.5, 'previous': 94.1, 'target': 98, 'limit': 95, 'unit': '%', 'decimals': 1, 'scale_max': 100,
     'description': 'System stock matching physical counts.'},
    {'key': 'on_time_delivery', 'name': 'On-Time Supplier Delivery', 'goal': 'increase',
     'value': 82, 'previous': 85, 'target': 95, 'limit': 85, 'unit': '%', 'decimals': 0, 'scale_max': 100,
     'description': 'Orders delivered by the expected date.'},
    # value is filled in from the request list in get_dashboard_context()
    {'key': 'delayed_orders', 'name': 'Delayed / Incomplete Orders', 'goal': 'decrease',
     'value': None, 'previous': 3, 'target': 0, 'limit': 2, 'unit': 'orders', 'decimals': 0, 'scale_max': 10,
     'description': 'Open orders currently marked delayed.'},
    {'key': 'emergency_orders', 'name': 'Emergency Replenishments', 'goal': 'decrease',
     'value': None, 'previous': 1, 'target': 0, 'limit': 1, 'unit': 'orders', 'decimals': 0, 'scale_max': 10,
     'description': 'Urgent orders raised outside the normal cycle.'},
]


def _build_sample_requests(today):
    """Sample reorder requests, dated relative to today so the demo stays current."""
    def days_ago(n):
        return today - timedelta(days=n)

    return [
        {'medicine': 'Ibuprofen 400mg', 'quantity': 300, 'supplier': 'MediSupply SA', 'status': 'Awaiting Approval',
         'request_date': days_ago(4), 'status_since': days_ago(4), 'expected_delivery': today + timedelta(days=10),
         'emergency': True, 'notes': ''},
        {'medicine': 'Insulin Glargine 100U/ml', 'quantity': 120, 'supplier': 'HealthCore Wholesale', 'status': 'Awaiting Approval',
         'request_date': days_ago(1), 'status_since': days_ago(1), 'expected_delivery': today + timedelta(days=21),
         'emergency': True, 'notes': ''},
        {'medicine': 'Paracetamol 500mg', 'quantity': 500, 'supplier': 'PharmaLink Distributors', 'status': 'Approved',
         'request_date': days_ago(3), 'status_since': days_ago(1), 'expected_delivery': today + timedelta(days=7),
         'emergency': False, 'notes': ''},
        {'medicine': 'Salbutamol Inhaler', 'quantity': 80, 'supplier': 'MediSupply SA', 'status': 'Ordered',
         'request_date': days_ago(6), 'status_since': days_ago(3), 'expected_delivery': today + timedelta(days=5),
         'emergency': False, 'notes': ''},
        {'medicine': 'Metformin 500mg', 'quantity': 400, 'supplier': 'Afrimed Logistics', 'status': 'In Transit',
         'request_date': days_ago(16), 'status_since': days_ago(5), 'expected_delivery': days_ago(2),
         'emergency': False, 'notes': ''},
        {'medicine': 'Amoxicillin 250mg', 'quantity': 250, 'supplier': 'PharmaLink Distributors', 'status': 'Delivered',
         'request_date': days_ago(14), 'status_since': days_ago(2), 'expected_delivery': days_ago(3),
         'emergency': False, 'notes': ''},
        {'medicine': 'Tenofovir/Emtricitabine', 'quantity': 180, 'supplier': 'HealthCore Wholesale', 'status': 'Delayed',
         'request_date': days_ago(20), 'status_since': days_ago(6), 'expected_delivery': days_ago(6),
         'emergency': False, 'notes': ''},
        {'medicine': 'Amoxicillin 250mg', 'quantity': 100, 'supplier': 'Afrimed Logistics', 'status': 'Delayed',
         'request_date': days_ago(18), 'status_since': days_ago(4), 'expected_delivery': days_ago(1),
         'emergency': False, 'notes': ''},
    ]


# In-memory request store: orders placed through the form are lost on restart
# until the database replaces this in Step 3.
REQUESTS = _build_sample_requests(date.today())

# Give every request an id so the API can find it (PATCH /api/requests/<id>/status)
for number, sample in enumerate(REQUESTS, start=1):
    sample['id'] = number


def _format_number(value, decimals):
    return f'{value:,.{decimals}f}'


def _with_unit(text, unit):
    return f'{text}{unit}' if unit == '%' else f'{text} {unit}'


def _days(n):
    return f"{n} day{'' if n == 1 else 's'}"


def _kpi_status(value, goal, target, limit):
    if goal == 'decrease':
        if value <= target:
            return 'good'
        return 'warning' if value <= limit else 'critical'
    if value >= target:
        return 'good'
    return 'warning' if value >= limit else 'critical'


def build_kpis(requests):
    derived = {
        'delayed_orders': sum(1 for r in requests if r['status'] == 'Delayed'),
        'emergency_orders': sum(1 for r in requests if r['emergency']),
    }
    kpis = []
    for definition in KPI_DEFINITIONS:
        kpi = dict(definition)
        if kpi['value'] is None:
            kpi['value'] = derived[kpi['key']]

        value, decimals = kpi['value'], kpi['decimals']
        delta = value - kpi['previous']
        if delta == 0:
            direction, improving = 'flat', None
        else:
            direction = 'up' if delta > 0 else 'down'
            improving = (delta < 0) if kpi['goal'] == 'decrease' else (delta > 0)

        target_word = 'at most' if kpi['goal'] == 'decrease' else 'at least'
        kpi.update({
            'status': _kpi_status(value, kpi['goal'], kpi['target'], kpi['limit']),
            'display_value': _format_number(value, decimals),
            'target_text': f"Target: {target_word} {_with_unit(_format_number(kpi['target'], decimals), kpi['unit'])}",
            'trend_direction': direction,
            'trend_improving': improving,
            'trend_text': f"{_format_number(abs(delta), decimals)} vs last month",
            'progress_percent': round(min(max(value / kpi['scale_max'], 0), 1) * 100),
        })
        kpis.append(kpi)
    return kpis


def build_inventory():
    inventory = []
    for med in MEDICINES:
        safety_stock = calculate_safety_stock(SERVICE_LEVEL_Z, med['demand_std_dev'], med['lead_time_days'])
        reorder_point = calculate_reorder_point(med['avg_daily_demand'], med['lead_time_days'], safety_stock)
        stock = med['current_stock']
        if stock < safety_stock:
            status = 'Critical'
        elif stock <= reorder_point:
            status = 'Low'
        else:
            status = 'Sufficient'
        inventory.append({
            'name': med['name'],
            'current_stock': stock,
            'reorder_point': round(reorder_point),
            'safety_stock': round(safety_stock),
            'status': status,
        })
    return inventory


def build_request_rows(requests, today):
    rows = []
    for r in sorted(requests, key=lambda r: r['request_date'], reverse=True):
        days_in_status = (today - r['status_since']).days
        overdue = r['status'] in OPEN_STATUSES and r['expected_delivery'] < today
        stalled = r['status'] == 'Awaiting Approval' and days_in_status > APPROVAL_SLA_DAYS
        rows.append({
            **r,
            'status_class': REQUEST_STATUSES[r['status']],
            'days_in_status': days_in_status,
            'needs_attention': overdue or stalled or r['status'] == 'Delayed',
            'next_status': NEXT_STATUS.get(r['status']),
            'next_action': ACTION_LABELS.get(NEXT_STATUS.get(r['status'])),
        })
    return rows


def build_alerts(kpis, request_rows, today):
    alerts = []
    for kpi in kpis:
        if kpi['status'] == 'critical':
            alerts.append({
                'type': 'kpi', 'severity': 'critical',
                'title': f"{kpi['name']} is critical",
                'message': f"Currently {_with_unit(kpi['display_value'], kpi['unit'])}. {kpi['target_text']}.",
            })
    for r in request_rows:
        label = f"{r['medicine']} ({r['quantity']:,} units)"
        if r['status'] == 'Delayed':
            overdue_days = (today - r['expected_delivery']).days
            alerts.append({
                'type': 'delayed', 'severity': 'critical',
                'title': f"Delayed order: {label}",
                'message': f"{_days(overdue_days)} past the expected delivery date. Follow up with {r['supplier']}.",
            })
        elif r['status'] == 'Awaiting Approval' and r['days_in_status'] > APPROVAL_SLA_DAYS:
            alerts.append({
                'type': 'approval', 'severity': 'critical' if r['emergency'] else 'warning',
                'title': f"Approval bottleneck: {label}",
                'message': (f"Waiting {_days(r['days_in_status'])} for approval (SLA: {_days(APPROVAL_SLA_DAYS)})."
                            + (" This is an emergency order." if r['emergency'] else "")),
            })
        elif r['status'] in OPEN_STATUSES and r['expected_delivery'] < today:
            overdue_days = (today - r['expected_delivery']).days
            alerts.append({
                'type': 'delivery', 'severity': 'warning',
                'title': f"Delivery overdue: {label}",
                'message': f"{r['status']} with {r['supplier']}, {_days(overdue_days)} past the expected date.",
            })
    severity_order = {'critical': 0, 'warning': 1}
    alerts.sort(key=lambda a: severity_order[a['severity']])
    return alerts



def validate_order(form, today=None):
    """
    Validate a submitted order form.

    Returns (order, errors): order is a dict ready for add_request() when
    errors is empty; errors maps field name -> message.
    """
    today = today or date.today()
    errors = {}

    medicine = form.get('medicine', '').strip()
    if medicine not in [m['name'] for m in MEDICINES]:
        errors['medicine'] = 'Choose a medicine from the list.'

    quantity = None
    try:
        quantity = int(form.get('quantity', ''))
        if not 1 <= quantity <= MAX_ORDER_QUANTITY:
            raise ValueError
    except ValueError:
        errors['quantity'] = f'Enter a whole number between 1 and {MAX_ORDER_QUANTITY:,}.'

    supplier = form.get('supplier', '').strip()
    if supplier not in SUPPLIERS:
        errors['supplier'] = 'Choose a supplier from the list.'

    expected_delivery = None
    try:
        expected_delivery = date.fromisoformat(form.get('expected_delivery', ''))
        if expected_delivery < today:
            errors['expected_delivery'] = 'Expected delivery cannot be in the past.'
    except ValueError:
        errors['expected_delivery'] = 'Choose an expected delivery date.'

    notes = form.get('notes', '').strip()
    if len(notes) > MAX_NOTES_LENGTH:
        errors['notes'] = f'Keep notes under {MAX_NOTES_LENGTH} characters.'

    if errors:
        return None, errors
    return {
        'medicine': medicine,
        'quantity': quantity,
        'supplier': supplier,
        'expected_delivery': expected_delivery,
        'notes': notes,
    }, {}


def add_request(order, today=None, emergency=False):
    """Store a validated order as a new request and return it. New orders always start as Awaiting Approval."""
    today = today or date.today()
    new_request = {
        **order,
        'id': max((r['id'] for r in REQUESTS), default=0) + 1,
        'status': 'Awaiting Approval',
        'request_date': today,
        'status_since': today,
        'emergency': emergency,
    }
    REQUESTS.append(new_request)
    return new_request


def filter_medicines_by_category(category):
    """Filter medicines by category. 'all' returns all medicines."""
    if category == 'all':
        return MEDICINES
    return [m for m in MEDICINES if m['category'] == category]


def filter_requests_by_category(requests, category):
    """Filter requests by medicine category."""
    if category == 'all':
        return requests
    medicine_names = {m['name'] for m in filter_medicines_by_category(category)}
    return [r for r in requests if r['medicine'] in medicine_names]


def get_dashboard_context(category='all'):
    """Everything index.html needs, as template variables.
    
    Args:
        category: Filter by medicine category ('all', 'antibiotics', 'analgesics', 'antiretrovirals', 'vaccines')
    """
    today = date.today()
    
    # Filter requests by category
    filtered_requests = filter_requests_by_category(REQUESTS, category)
    
    # Build KPIs from filtered requests
    kpis = build_kpis(filtered_requests)
    request_rows = build_request_rows(filtered_requests, today)
    
    # Filter medicines and inventory by category
    filtered_medicines = filter_medicines_by_category(category)
    
    return {
        'today': today,
        'metrics': kpis,
        'requests': request_rows,
        'alerts': build_alerts(kpis, request_rows, today),
        'inventory': [inv for inv in build_inventory() if any(m['name'] == inv['name'] for m in filtered_medicines)],
        'medicine_options': [m['name'] for m in filtered_medicines],
        'supplier_options': SUPPLIERS,
        'current_category': category,
    }
    


# Adding medicines (Flow 1: form -> POST /api/medicines -> inventory table)


MEDICINE_CATEGORIES = ['analgesics', 'antibiotics', 'antidiabetics', 'antiretrovirals', 'respiratory', 'vaccines']
MAX_NAME_LENGTH = 100


def _read_number(data, field, errors, minimum, whole=False):
    """Read one numeric field, adding an error message if it is missing or out of range."""
    try:
        value = float(data.get(field, ''))
        if not math.isfinite(value):
            raise ValueError
        if whole and not value.is_integer():
            raise ValueError
        if value < minimum:
            raise ValueError
        return int(value) if whole else value
    except (TypeError, ValueError):
        kind = 'a whole number' if whole else 'a number'
        errors[field] = f'Enter {kind} of at least {minimum}.'
        return None


def validate_medicine(data):
    """
    Validate a new medicine sent to POST /api/medicines.

    Returns (medicine, errors): medicine is a dict ready for add_medicine()
    when errors is empty; errors maps field name -> message.
    """
    errors = {}

    name = str(data.get('name', '')).strip()
    if not name:
        errors['name'] = 'Enter the medicine name.'
    elif len(name) > MAX_NAME_LENGTH:
        errors['name'] = f'Keep the name under {MAX_NAME_LENGTH} characters.'

    category = str(data.get('category', '')).strip().lower()
    if category not in MEDICINE_CATEGORIES:
        errors['category'] = 'Choose a category from the list.'

    current_stock = _read_number(data, 'current_stock', errors, minimum=0, whole=True)
    avg_daily_demand = _read_number(data, 'avg_daily_demand', errors, minimum=0)
    demand_std_dev = _read_number(data, 'demand_std_dev', errors, minimum=0)
    lead_time_days = _read_number(data, 'lead_time_days', errors, minimum=1, whole=True)

    if errors:
        return None, errors
    return {
        'name': name,
        'category': category,
        'current_stock': current_stock,
        'avg_daily_demand': avg_daily_demand,
        'demand_std_dev': demand_std_dev,
        'lead_time_days': lead_time_days,
    }, {}


def medicine_exists(name):
    """True if a medicine with this name is already stored (ignores capital letters)."""
    return any(m['name'].lower() == name.lower() for m in MEDICINES)


def add_medicine(medicine):
    """Store a validated medicine and return its inventory row (with reorder point and status)."""
    MEDICINES.append(medicine)
    row = next(item for item in build_inventory() if item['name'] == medicine['name'])
    return {**row, 'category': medicine['category']}


# ---------------------------------------------------------------------------
# Reordering (Flow 2: EOQ recommendation -> request -> status steps -> stock update)

# EOQ cost assumptions (placeholder values until real costs come from the database)
ORDER_COST = 500               # R per order placed (admin and delivery)
HOLDING_COST_PER_UNIT = 4      # R to store one unit for a year (storage, expiry risk)
DAYS_PER_YEAR = 365

# Each status moves to exactly one next status. Delivered is the end.
# A Delayed order is already on its way, so its next step is Delivered.
NEXT_STATUS = {
    'Awaiting Approval': 'Approved',
    'Approved': 'Ordered',
    'Ordered': 'In Transit',
    'In Transit': 'Delivered',
    'Delayed': 'Delivered',
}

# Button text for moving a request to each status
ACTION_LABELS = {
    'Approved': 'Approve',
    'Ordered': 'Mark ordered',
    'In Transit': 'Mark in transit',
    'Delivered': 'Mark delivered',
}


def find_medicine(name):
    """Return the stored medicine with this name, or None."""
    return next((m for m in MEDICINES if m['name'] == name), None)


def inventory_row(name):
    """Return one medicine's inventory row (stock, reorder point, status), or None."""
    return next((item for item in build_inventory() if item['name'] == name), None)


def recommend_order(name):
    """
    Use the EOQ model to recommend how many units of a medicine to order.

    Returns None if the medicine does not exist.
    """
    medicine = find_medicine(name)
    if medicine is None:
        return None
    annual_demand = medicine['avg_daily_demand'] * DAYS_PER_YEAR
    eoq = calculate_eoq(annual_demand, ORDER_COST, HOLDING_COST_PER_UNIT)
    row = inventory_row(name)
    return {
        'medicine': name,
        'recommended_quantity': max(1, round(eoq)),
        'annual_demand': round(annual_demand),
        'order_cost': ORDER_COST,
        'holding_cost': HOLDING_COST_PER_UNIT,
        'current_stock': row['current_stock'],
        'reorder_point': row['reorder_point'],
        'status': row['status'],
    }


def request_to_json(r):
    """Convert a stored request into JSON-friendly values (dates as YYYY-MM-DD)."""
    return {
        'id': r['id'],
        'medicine': r['medicine'],
        'quantity': r['quantity'],
        'supplier': r['supplier'],
        'status': r['status'],
        'status_class': REQUEST_STATUSES[r['status']],
        'request_date': r['request_date'].isoformat(),
        'expected_delivery': r['expected_delivery'].isoformat(),
        'emergency': r['emergency'],
        'notes': r.get('notes', ''),
        'next_status': NEXT_STATUS.get(r['status']),
        'next_action': ACTION_LABELS.get(NEXT_STATUS.get(r['status'])),
    }


def advance_request(request_id, today=None):
    """
    Move a request to its next status. When it becomes Delivered, the
    delivered quantity is added to the medicine's current stock.

    Returns (request, error): error is a message when the request
    cannot move (not found, or already delivered).
    """
    today = today or date.today()
    found = next((r for r in REQUESTS if r['id'] == request_id), None)
    if found is None:
        return None, f'Request {request_id} was not found.'

    next_status = NEXT_STATUS.get(found['status'])
    if next_status is None:
        return None, f"Request {request_id} is already {found['status']}."

    found['status'] = next_status
    found['status_since'] = today

    if next_status == 'Delivered':
        medicine = find_medicine(found['medicine'])
        if medicine is not None:
            medicine['current_stock'] += found['quantity']

    return found, None


# Live list endpoints (replace the mock JSON in static/mock/)
INVENTORY_STATUSES = ('Critical', 'Low', 'Sufficient')


def medicine_to_json(medicine_id, medicine):
    """One medicine with its EOQ-model figures, in the same shape as the old medicines.json."""
    row = inventory_row(medicine['name'])
    return {
        'id': medicine_id,
        'name': medicine['name'],
        'category': medicine['category'],
        'current_stock': medicine['current_stock'],
        'avg_daily_demand': medicine['avg_daily_demand'],
        'demand_std_dev': medicine['demand_std_dev'],
        'lead_time_days': medicine['lead_time_days'],
        'reorder_point': row['reorder_point'],
        'safety_stock': row['safety_stock'],
        'status': row['status'],
    }


def list_medicines(category='all', status=None):
    """All medicines as JSON rows, optionally filtered by category and stock status."""
    rows = [medicine_to_json(number, m) for number, m in enumerate(MEDICINES, start=1)]
    if category != 'all':
        rows = [r for r in rows if r['category'] == category]
    if status:
        rows = [r for r in rows if r['status'] == status]
    return rows


def list_requests(status=None):
    """All reorder requests as JSON rows, optionally filtered by status."""
    rows = [request_to_json(r) for r in REQUESTS]
    if status:
        rows = [r for r in rows if r['status'] == status]
    return rows


def list_kpis(category='all'):
    """The dashboard KPIs, calculated live from the current requests."""
    fields = ('key', 'name', 'value', 'display_value', 'previous', 'target', 'unit', 'status',
              'progress_percent', 'trend_direction', 'trend_improving', 'trend_text', 'target_text', 'description')
    kpis = build_kpis(filter_requests_by_category(REQUESTS, category))
    return [{field: kpi[field] for field in fields} for kpi in kpis]


# ---------------------------------------------------------------------------
# Live stock metrics (B3.3: calculated from current stock, orders and the EOQ model)
# ---------------------------------------------------------------------------

def _metric(key, name, value, unit, description, status='good'):
    """One metric card's data."""
    return {'key': key, 'name': name, 'value': value, 'display_value': f'{value:,}',
            'unit': unit, 'description': description, 'status': status}


def live_metrics(category='all'):
    """
    Totals and supply chain KPIs worked out from the data right now, so they
    change as soon as stock, medicines or orders change.
    """
    names = {m['name'] for m in filter_medicines_by_category(category)}
    inventory = [item for item in build_inventory() if item['name'] in names]
    requests = filter_requests_by_category(REQUESTS, category)

    to_restock = [item for item in inventory if item['status'] != 'Sufficient']
    critical = [item for item in inventory if item['status'] == 'Critical']
    open_requests = [r for r in requests if r['status'] != 'Delivered']
    eoq_to_order = sum(recommend_order(item['name'])['recommended_quantity'] for item in to_restock)

    return [
        _metric('medicines_tracked', 'Medicines tracked', len(inventory), 'items',
                'Medicines in the inventory.'),
        _metric('units_in_stock', 'Units in stock', sum(item['current_stock'] for item in inventory), 'units',
                'All medicines combined.'),
        _metric('items_to_restock', 'Items to restock', len(to_restock), 'items',
                'At or below their reorder point.', 'warning' if to_restock else 'good'),
        _metric('critical_stock', 'Critical stock', len(critical), 'items',
                'Below safety stock: stockout risk.', 'critical' if critical else 'good'),
        _metric('open_orders', 'Open reorder requests', len(open_requests), 'orders',
                'Requested but not yet delivered.'),
        _metric('eoq_to_order', 'EOQ to order', eoq_to_order, 'units',
                'EOQ-recommended quantity for the items to restock.', 'warning' if eoq_to_order else 'good'),
    ]