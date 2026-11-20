"""
Delivery and facility data for the tracking board.

Placeholder data until the MySQL database is connected (Step 3).
"""

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


# ---------------------------------------------------------------------------
# Updating deliveries (Flow 3: board modal -> PATCH /api/deliveries/<id> -> board and KPIs)


DELIVERY_STATUSES = ['Scheduled', 'In Transit', 'Delayed', 'Delivered', 'Failed']
PROBLEM_STATUSES = ('Delayed', 'Failed')     # these must say what went wrong
MIN_EXCEPTION_LENGTH = 5
MAX_EXCEPTION_LENGTH = 300


def find_delivery(delivery_id):
    """Return the delivery with this id, or None."""
    return next((d for d in DELIVERIES if d['id'] == delivery_id), None)


def validate_delivery_update(data):
    """
    Validate a status/exception update sent to PATCH /api/deliveries/<id>.

    Returns (changes, errors): changes is a dict ready for update_delivery()
    when errors is empty; errors maps field name -> message.
    """
    errors = {}

    status = str(data.get('status', '')).strip()
    if status not in DELIVERY_STATUSES:
        errors['status'] = 'Choose a status from the list.'

    exception = str(data.get('exception', '')).strip()
    if len(exception) > MAX_EXCEPTION_LENGTH:
        errors['exception'] = f'Keep the exception under {MAX_EXCEPTION_LENGTH} characters.'
    elif status in PROBLEM_STATUSES and len(exception) < MIN_EXCEPTION_LENGTH:
        errors['exception'] = f'Describe what went wrong (at least {MIN_EXCEPTION_LENGTH} characters).'

    if errors:
        return None, errors
    return {'status': status, 'exception': exception}, {}


def update_delivery(delivery, changes):
    """Apply a validated update and return the delivery."""
    delivery['status'] = changes['status']
    delivery['exception'] = changes['exception']
    return delivery


def delivery_summary():
    """
    Delivery KPIs calculated from the current deliveries, so the board and
    the KPI page always match the latest updates.
    """
    total = len(DELIVERIES)
    delivered = sum(1 for d in DELIVERIES if d['status'] == 'Delivered')
    return {
        'total': total,
        'in_transit': sum(1 for d in DELIVERIES if d['status'] == 'In Transit'),
        'problems': sum(1 for d in DELIVERIES if d['status'] in PROBLEM_STATUSES),
        'delivered': delivered,
        'delivered_percent': round(delivered / total * 100) if total else 0,
        'open_exceptions': sum(1 for d in DELIVERIES if d['exception'] and d['status'] != 'Delivered'),
    }


