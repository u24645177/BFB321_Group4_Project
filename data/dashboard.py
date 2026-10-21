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

from datetime import date, timedelta

from models.eoq import calculate_reorder_point, calculate_safety_stock

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
    {'name': 'Metformin 500mg', 'category': 'antiretrovirals', 'current_stock': 260, 'avg_daily_demand': 8, 'demand_std_dev': 2, 'lead_time_days': 14},
    {'name': 'Insulin Glargine 100U/ml', 'category': 'vaccines', 'current_stock': 6, 'avg_daily_demand': 3, 'demand_std_dev': 1, 'lead_time_days': 21},
    {'name': 'Salbutamol Inhaler', 'category': 'antibiotics', 'current_stock': 58, 'avg_daily_demand': 5, 'demand_std_dev': 2, 'lead_time_days': 10},
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


def add_request(order, today=None):
    """Store a validated order as a new request. New orders always start as Awaiting Approval."""
    today = today or date.today()
    REQUESTS.append({
        **order,
        'status': 'Awaiting Approval',
        'request_date': today,
        'status_since': today,
        'emergency': False,
    })

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
    
