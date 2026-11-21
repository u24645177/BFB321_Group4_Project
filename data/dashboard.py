"""
Dashboard Data: inventory, reorder requests, KPIs and alerts, stored in MySQL.

The routes call the functions below and never see any SQL. Every read and
write goes through db.py, which uses parameterised queries (%s) and wraps
writes in a transaction that rolls back if anything fails.

Only raw records are stored. Everything shown as a status (stock level,
days in status, alerts, KPI colours) is worked out from them here:
    - Reorder points, safety stock and EOQ come from models/eoq.py.
    - Inventory is Critical below safety stock, Low at or below the reorder point.
    - Alerts come from critical KPIs, delayed or overdue orders and
      requests waiting longer than the approval SLA.

Stock levels are shown for one facility (DEFAULT_FACILITY_ID). Orders and
deliveries cover every facility.
"""

import math
from datetime import date, datetime

from db import fetch_all, fetch_one, transaction
from models.eoq import calculate_eoq, calculate_reorder_point, calculate_safety_stock

SERVICE_LEVEL_Z = 1.65      # 95% service level
APPROVAL_SLA_DAYS = 2       # requests waiting longer than this are a bottleneck
MAX_ORDER_QUANTITY = 100_000
MAX_NOTES_LENGTH = 500
DAYS_PER_YEAR = 365

DEFAULT_FACILITY_ID = 1     # Steve Biko Academic Hospital in the seed data

# Used when a new medicine is added without its costs. A R20 unit cost at a
# 20% holding rate gives R4 per unit per year, the team's original assumption.
DEFAULT_UNIT_COST = 20.00
DEFAULT_ORDER_COST = 500.00
DEFAULT_HOLDING_RATE = 0.20

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
INVENTORY_STATUSES = ('Critical', 'Low', 'Sufficient')

MEDICINE_CATEGORIES = ['analgesics', 'antibiotics', 'antidiabetics', 'antiretrovirals', 'respiratory', 'vaccines']
MAX_NAME_LENGTH = 100

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


# ---------------------------------------------------------------------------
# Reading from the database
# ---------------------------------------------------------------------------

MEDICINE_SELECT = """
    SELECT m.medicine_id, m.name, m.category, m.unit_cost, m.order_cost, m.holding_rate,
           m.avg_daily_demand, m.demand_std_dev, m.lead_time_days,
           COALESCE(i.quantity_on_hand, 0) AS current_stock
    FROM medicines m
    LEFT JOIN inventory i ON i.medicine_id = m.medicine_id AND i.facility_id = %s
    WHERE m.is_active = TRUE
"""


def get_medicines(category='all', facility_id=DEFAULT_FACILITY_ID):
    """Active medicines with their stock at one facility, optionally for one category."""
    sql, params = MEDICINE_SELECT, [facility_id]
    if category != 'all':
        sql += " AND m.category = %s"
        params.append(category)
    return fetch_all(sql + " ORDER BY m.name", params)


def find_medicine(name, facility_id=DEFAULT_FACILITY_ID):
    """Return the stored medicine with this name (with its stock), or None."""
    return fetch_one(MEDICINE_SELECT + " AND m.name = %s", (facility_id, name))


def get_supplier_names():
    """Supplier names for the order form drop-downs."""
    return [row['name'] for row in fetch_all("SELECT name FROM suppliers ORDER BY name")]


REQUEST_SELECT = """
    SELECT o.order_id, m.name AS medicine, m.category, o.quantity, s.name AS supplier, o.status,
           o.requested_at, o.status_changed_at, o.expected_delivery, o.is_emergency, o.notes
    FROM orders o
    JOIN medicines m ON m.medicine_id = o.medicine_id
    JOIN suppliers s ON s.supplier_id = o.supplier_id
"""


def _request_from_row(row):
    """Shape one orders row like the request dicts the templates and API use."""
    return {
        'id': row['order_id'],
        'medicine': row['medicine'],
        'quantity': row['quantity'],
        'supplier': row['supplier'],
        'status': row['status'],
        'request_date': row['requested_at'].date(),
        'status_since': row['status_changed_at'].date(),
        'expected_delivery': row['expected_delivery'],
        'emergency': bool(row['is_emergency']),
        'notes': row['notes'] or '',
    }


def get_requests(category='all', status=None):
    """
    Reorder requests, newest first. Cancelled orders are left out because
    the dashboard has no badge for them.
    """
    sql, params = REQUEST_SELECT + " WHERE o.status <> 'Cancelled'", []
    if category != 'all':
        sql += " AND m.category = %s"
        params.append(category)
    if status:
        sql += " AND o.status = %s"
        params.append(status)
    return [_request_from_row(row) for row in fetch_all(sql + " ORDER BY o.requested_at DESC", params)]


def get_request(request_id):
    """One request by id, or None."""
    row = fetch_one(REQUEST_SELECT + " WHERE o.order_id = %s", (request_id,))
    return _request_from_row(row) if row else None


# ---------------------------------------------------------------------------
# KPIs and dashboard rows
# ---------------------------------------------------------------------------

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


def stock_status(stock, safety_stock, reorder_point):
    """Critical below safety stock, Low at or below the reorder point, otherwise Sufficient."""
    if stock < safety_stock:
        return 'Critical'
    if stock <= reorder_point:
        return 'Low'
    return 'Sufficient'


def _inventory_from_medicine(med):
    """Stock, reorder point, safety stock and status for one medicine row."""
    safety_stock = calculate_safety_stock(SERVICE_LEVEL_Z, float(med['demand_std_dev']), med['lead_time_days'])
    reorder_point = calculate_reorder_point(float(med['avg_daily_demand']), med['lead_time_days'], safety_stock)
    return {
        'name': med['name'],
        'current_stock': med['current_stock'],
        'reorder_point': round(reorder_point),
        'safety_stock': round(safety_stock),
        'status': stock_status(med['current_stock'], safety_stock, reorder_point),
    }


def build_inventory(category='all'):
    """Inventory table rows for the dashboard and reorder form."""
    return [_inventory_from_medicine(med) for med in get_medicines(category)]


def inventory_row(name):
    """Return one medicine's inventory row (stock, reorder point, status), or None."""
    med = find_medicine(name)
    return _inventory_from_medicine(med) if med else None


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


# ---------------------------------------------------------------------------
# Placing orders (dashboard form and POST /api/requests)
# ---------------------------------------------------------------------------

def validate_order(form, today=None):
    """
    Validate a submitted order form.

    Returns (order, errors): order is a dict ready for add_request() when
    errors is empty; errors maps field name -> message.
    """
    today = today or date.today()
    errors = {}

    medicine = form.get('medicine', '').strip()
    if find_medicine(medicine) is None:
        errors['medicine'] = 'Choose a medicine from the list.'

    quantity = None
    try:
        quantity = int(form.get('quantity', ''))
        if not 1 <= quantity <= MAX_ORDER_QUANTITY:
            raise ValueError
    except ValueError:
        errors['quantity'] = f'Enter a whole number between 1 and {MAX_ORDER_QUANTITY:,}.'

    supplier = form.get('supplier', '').strip()
    if supplier not in get_supplier_names():
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


def add_request(order, today=None, emergency=False, facility_id=DEFAULT_FACILITY_ID):
    """
    Save a validated order and return it. New orders always start as
    Awaiting Approval. The medicine's unit cost is copied onto the order so
    it keeps the price paid even if the catalogue price changes later.
    """
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO orders (medicine_id, facility_id, supplier_id, quantity, unit_cost,
                                status, is_emergency, notes, expected_delivery)
            SELECT m.medicine_id, %s, s.supplier_id, %s, m.unit_cost,
                   'Awaiting Approval', %s, %s, %s
            FROM medicines m JOIN suppliers s ON s.name = %s
            WHERE m.name = %s
            """,
            (facility_id, order['quantity'], bool(emergency), order['notes'] or None,
             order['expected_delivery'], order['supplier'], order['medicine']),
        )
        new_id = cur.lastrowid
    return get_request(new_id)


# ---------------------------------------------------------------------------
# Everything the dashboard template needs
# ---------------------------------------------------------------------------

def get_dashboard_context(category='all'):
    """Everything index.html needs, as template variables.

    Args:
        category: 'all' or one of MEDICINE_CATEGORIES
    """
    if category != 'all' and category not in MEDICINE_CATEGORIES:
        category = 'all'
    today = date.today()

    requests = get_requests(category)
    kpis = build_kpis(requests)
    request_rows = build_request_rows(requests, today)
    inventory = build_inventory(category)

    return {
        'today': today,
        'metrics': kpis,
        'requests': request_rows,
        'alerts': build_alerts(kpis, request_rows, today),
        'inventory': inventory,
        'medicine_options': [item['name'] for item in inventory],
        'supplier_options': get_supplier_names(),
        'current_category': category,
    }


# ---------------------------------------------------------------------------
# Adding medicines (Flow 1: form -> POST /api/medicines -> inventory table)
# ---------------------------------------------------------------------------

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


def _read_optional_cost(data, field, errors, default):
    """A cost in rand that may be left out, in which case the default is used."""
    if data.get(field) in (None, ''):
        return default
    value = _read_number(data, field, errors, minimum=0.01)
    return round(value, 2) if value is not None else None


def validate_medicine(data):
    """
    Validate a new medicine sent to POST /api/medicines.

    Returns (medicine, errors): medicine is a dict ready for add_medicine()
    when errors is empty; errors maps field name -> message.
    unit_cost and order_cost are optional (defaults above).
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
    unit_cost = _read_optional_cost(data, 'unit_cost', errors, DEFAULT_UNIT_COST)
    order_cost = _read_optional_cost(data, 'order_cost', errors, DEFAULT_ORDER_COST)

    if errors:
        return None, errors
    return {
        'name': name,
        'category': category,
        'current_stock': current_stock,
        'avg_daily_demand': avg_daily_demand,
        'demand_std_dev': demand_std_dev,
        'lead_time_days': lead_time_days,
        'unit_cost': unit_cost,
        'order_cost': order_cost,
    }, {}


def medicine_exists(name):
    """True if a medicine with this name is already stored (MySQL ignores capital letters here)."""
    return fetch_one("SELECT medicine_id FROM medicines WHERE name = %s", (name,)) is not None


def add_medicine(medicine, facility_id=DEFAULT_FACILITY_ID):
    """
    Save a validated medicine and return its inventory row.

    The medicine and one inventory row per facility are written in a single
    transaction: the given stock goes to this facility, the others start at 0.
    If any insert fails, nothing is saved.
    """
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO medicines (name, category, unit_cost, order_cost, holding_rate,
                                   avg_daily_demand, demand_std_dev, lead_time_days)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (medicine['name'], medicine['category'], medicine['unit_cost'], medicine['order_cost'],
             DEFAULT_HOLDING_RATE, medicine['avg_daily_demand'], medicine['demand_std_dev'],
             medicine['lead_time_days']),
        )
        medicine_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO inventory (medicine_id, facility_id, quantity_on_hand)
            SELECT %s, f.facility_id, IF(f.facility_id = %s, %s, 0)
            FROM facilities f
            """,
            (medicine_id, facility_id, medicine['current_stock']),
        )
    return {**_inventory_from_medicine(medicine), 'category': medicine['category']}


# ---------------------------------------------------------------------------
# Reordering (Flow 2: EOQ recommendation -> request -> status steps -> stock update)
# ---------------------------------------------------------------------------

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


def _eoq_inputs(med):
    """Annual demand, order cost (S) and holding cost per unit per year (H) for one medicine."""
    annual_demand = float(med['avg_daily_demand']) * DAYS_PER_YEAR
    order_cost = float(med['order_cost'])
    holding_cost = round(float(med['unit_cost']) * float(med['holding_rate']), 2)
    return annual_demand, order_cost, holding_cost


def _eoq_quantity(med):
    """EOQ order quantity for one medicine row, at least 1 unit."""
    annual_demand, order_cost, holding_cost = _eoq_inputs(med)
    return max(1, round(calculate_eoq(annual_demand, order_cost, holding_cost)))


def recommend_order(name):
    """
    Use the EOQ model to recommend how many units of a medicine to order,
    using that medicine's own order and holding costs from the database.

    Returns None if the medicine does not exist.
    """
    med = find_medicine(name)
    if med is None:
        return None
    annual_demand, order_cost, holding_cost = _eoq_inputs(med)
    row = _inventory_from_medicine(med)
    return {
        'medicine': name,
        'recommended_quantity': _eoq_quantity(med),
        'annual_demand': round(annual_demand),
        'order_cost': order_cost,
        'holding_cost': holding_cost,
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


# Delivery status that matches each order status, once a delivery exists
ORDER_TO_DELIVERY_STATUS = {'In Transit': 'In Transit', 'Delayed': 'Delayed', 'Delivered': 'Delivered'}


def set_order_status(cur, order_id, new_status, sync_delivery=True):
    """
    Move an order to new_status inside an open transaction, keeping the
    related records consistent:
        - Approved:  records approved_at (used by the approval-time KPI).
        - Ordered:   creates its delivery on the board (Scheduled).
        - Delivered: records delivered_at and adds the quantity to the
                     facility's stock. This can only happen once per order.
    sync_delivery=False is used when the change came from the delivery itself.
    """
    cur.execute("SELECT status, expected_delivery FROM orders WHERE order_id = %s FOR UPDATE", (order_id,))
    order = cur.fetchone()
    if order is None or order['status'] == new_status or order['status'] == 'Delivered':
        return

    cur.execute(
        """
        UPDATE orders
        SET status = %s, status_changed_at = NOW(),
            approved_at  = IF(%s = 'Approved', NOW(), approved_at),
            delivered_at = IF(%s = 'Delivered', NOW(), delivered_at)
        WHERE order_id = %s
        """,
        (new_status, new_status, new_status, order_id),
    )

    if new_status == 'Delivered':
        cur.execute(
            """
            UPDATE inventory i
            JOIN orders o ON o.medicine_id = i.medicine_id AND o.facility_id = i.facility_id
            SET i.quantity_on_hand = i.quantity_on_hand + o.quantity
            WHERE o.order_id = %s
            """,
            (order_id,),
        )

    if not sync_delivery:
        return
    if new_status == 'Ordered':
        cur.execute(
            """
            INSERT IGNORE INTO deliveries (reference, order_id, eta, status)
            VALUES (CONCAT('DEL-', 2000 + %s), %s, TIMESTAMP(%s, '12:00:00'), 'Scheduled')
            """,
            (order_id, order_id, order['expected_delivery']),
        )
    elif new_status in ORDER_TO_DELIVERY_STATUS:
        cur.execute(
            """
            UPDATE deliveries
            SET status = %s, delivered_at = IF(%s = 'Delivered', NOW(), delivered_at)
            WHERE order_id = %s
            """,
            (ORDER_TO_DELIVERY_STATUS[new_status], new_status, order_id),
        )


def advance_request(request_id, today=None):
    """
    Move a request to its next status. When it becomes Delivered, the
    delivered quantity is added to the facility's stock.

    Returns (request, error): error is a message when the request
    cannot move (not found, or already delivered).
    """
    found = get_request(request_id)
    if found is None:
        return None, f'Request {request_id} was not found.'

    next_status = NEXT_STATUS.get(found['status'])
    if next_status is None:
        return None, f"Request {request_id} is already {found['status']}."

    with transaction() as cur:
        set_order_status(cur, request_id, next_status)
    return get_request(request_id), None


# ---------------------------------------------------------------------------
# Live list endpoints (GET /api/medicines, /api/requests, /api/kpis)
# ---------------------------------------------------------------------------

def medicine_to_json(med):
    """One medicine with its EOQ-model figures, in the shape the frontend expects."""
    row = _inventory_from_medicine(med)
    return {
        'id': med['medicine_id'],
        'name': med['name'],
        'category': med['category'],
        'current_stock': med['current_stock'],
        'avg_daily_demand': float(med['avg_daily_demand']),
        'demand_std_dev': float(med['demand_std_dev']),
        'lead_time_days': med['lead_time_days'],
        'reorder_point': row['reorder_point'],
        'safety_stock': row['safety_stock'],
        'status': row['status'],
    }


def list_medicines(category='all', status=None):
    """All medicines as JSON rows, optionally filtered by category and stock status."""
    rows = [medicine_to_json(med) for med in get_medicines(category)]
    if status:
        rows = [r for r in rows if r['status'] == status]
    return rows


def list_requests(status=None):
    """All reorder requests as JSON rows, optionally filtered by status."""
    return [request_to_json(r) for r in get_requests(status=status)]


def list_kpis(category='all'):
    """The dashboard KPIs, calculated from the current requests."""
    fields = ('key', 'name', 'value', 'display_value', 'previous', 'target', 'unit', 'status',
              'progress_percent', 'trend_direction', 'trend_improving', 'trend_text', 'target_text', 'description')
    kpis = build_kpis(get_requests(category))
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
    Totals and supply chain KPIs worked out from the database right now, so
    they change as soon as stock, medicines or orders change.
    """
    medicines = get_medicines(category)
    inventory = [_inventory_from_medicine(med) for med in medicines]
    requests = get_requests(category)

    to_restock = [med for med, item in zip(medicines, inventory) if item['status'] != 'Sufficient']
    critical = [item for item in inventory if item['status'] == 'Critical']
    open_requests = [r for r in requests if r['status'] != 'Delivered']
    eoq_to_order = sum(_eoq_quantity(med) for med in to_restock)
    stock_value = sum(med['current_stock'] * float(med['unit_cost']) for med in medicines)

    return [
        _metric('medicines_tracked', 'Medicines tracked', len(inventory), 'items',
                'Medicines in the inventory.'),
        _metric('units_in_stock', 'Units in stock', sum(item['current_stock'] for item in inventory), 'units',
                'All medicines combined.'),
        _metric('stock_value', 'Stock value', round(stock_value), 'rand',
                'Units in stock × unit cost.'),
        _metric('items_to_restock', 'Items to restock', len(to_restock), 'items',
                'At or below their reorder point.', 'warning' if to_restock else 'good'),
        _metric('critical_stock', 'Critical stock', len(critical), 'items',
                'Below safety stock: stockout risk.', 'critical' if critical else 'good'),
        _metric('open_orders', 'Open reorder requests', len(open_requests), 'orders',
                'Requested but not yet delivered.'),
        _metric('eoq_to_order', 'EOQ to order', eoq_to_order, 'units',
                'EOQ-recommended quantity for the items to restock.', 'warning' if eoq_to_order else 'good'),
    ]
