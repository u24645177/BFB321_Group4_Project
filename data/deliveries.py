"""
Delivery and facility data for the tracking board, stored in MySQL.

Flow 3: board modal -> PATCH /api/deliveries/<id> -> board and KPIs.
A delivery belongs to one order, so changing a delivery's status also moves
its order (and, once Delivered, adds the stock) in the same transaction.
"""

from db import fetch_all, fetch_one, transaction
from data.dashboard import set_order_status

DELIVERY_STATUSES = ['Scheduled', 'In Transit', 'Delayed', 'Delivered', 'Failed']
PROBLEM_STATUSES = ('Delayed', 'Failed')     # these must say what went wrong
MIN_EXCEPTION_LENGTH = 5
MAX_EXCEPTION_LENGTH = 255                   # matches deliveries.exception_note VARCHAR(255)

# Order status that follows from each delivery status (Scheduled leaves the order as it is)
DELIVERY_TO_ORDER_STATUS = {
    'In Transit': 'In Transit',
    'Delayed': 'Delayed',
    'Failed': 'Delayed',
    'Delivered': 'Delivered',
}

DELIVERY_SELECT = """
    SELECT d.reference, d.order_id, d.vehicle_reg, d.eta, d.status, d.exception_note,
           f.name AS facility
    FROM deliveries d
    JOIN orders o     ON o.order_id = d.order_id
    JOIN facilities f ON f.facility_id = o.facility_id
"""


def get_facility_names():
    """Facility names for the reorder form drop-down."""
    return [row['name'] for row in fetch_all("SELECT name FROM facilities ORDER BY name")]


def _delivery_from_row(row):
    """Shape one database row the way tracking.html, kpis.html and tracking.js expect it."""
    return {
        'id': row['reference'],
        'route': f"Depot → {row['facility']}",
        'vehicle': row['vehicle_reg'] or '—',
        'eta': row['eta'].strftime('%Y-%m-%d %H:%M'),
        'status': row['status'],
        'exception': row['exception_note'] or '',
    }


def get_deliveries():
    """Every delivery: active ones first (soonest ETA first), then delivered ones (newest first)."""
    sql = DELIVERY_SELECT + """
        ORDER BY d.status = 'Delivered',
                 CASE WHEN d.status = 'Delivered' THEN NULL ELSE d.eta END,
                 d.eta DESC
    """
    return [_delivery_from_row(row) for row in fetch_all(sql)]


def find_delivery(delivery_id):
    """Return the delivery with this reference (e.g. 'DEL-1042'), or None."""
    row = fetch_one(DELIVERY_SELECT + " WHERE d.reference = %s", (delivery_id,))
    return _delivery_from_row(row) if row else None


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

    exception = str(data.get('exception', '') or '').strip()
    if len(exception) > MAX_EXCEPTION_LENGTH:
        errors['exception'] = f'Keep the exception under {MAX_EXCEPTION_LENGTH} characters.'
    elif status in PROBLEM_STATUSES and len(exception) < MIN_EXCEPTION_LENGTH:
        errors['exception'] = f'Describe what went wrong (at least {MIN_EXCEPTION_LENGTH} characters).'

    if errors:
        return None, errors
    return {'status': status, 'exception': exception}, {}


def update_delivery(delivery, changes):
    """
    Save a validated update and return the delivery as it now is.

    The delivery and its order are updated in one transaction, so the board,
    the request list and the stock never disagree.
    """
    with transaction() as cur:
        cur.execute(
            """
            UPDATE deliveries
            SET status = %s, exception_note = %s,
                delivered_at = IF(%s = 'Delivered', COALESCE(delivered_at, NOW()), delivered_at)
            WHERE reference = %s
            """,
            (changes['status'], changes['exception'] or None, changes['status'], delivery['id']),
        )
        order_status = DELIVERY_TO_ORDER_STATUS.get(changes['status'])
        if order_status:
            cur.execute("SELECT order_id FROM deliveries WHERE reference = %s", (delivery['id'],))
            set_order_status(cur, cur.fetchone()['order_id'], order_status, sync_delivery=False)
    return find_delivery(delivery['id'])


def delivery_summary():
    """
    Delivery KPIs counted in the database, so the board and the KPI page
    always match the latest updates.
    """
    row = fetch_one(
        """
        SELECT COUNT(*) AS total,
               COALESCE(SUM(status = 'In Transit'), 0)              AS in_transit,
               COALESCE(SUM(status IN ('Delayed', 'Failed')), 0)    AS problems,
               COALESCE(SUM(status = 'Delivered'), 0)               AS delivered,
               COALESCE(SUM(exception_note IS NOT NULL AND exception_note <> ''
                            AND status <> 'Delivered'), 0)          AS open_exceptions
        FROM deliveries
        """
    )
    total, delivered = int(row['total']), int(row['delivered'])
    return {
        'total': total,
        'in_transit': int(row['in_transit']),
        'problems': int(row['problems']),
        'delivered': delivered,
        'delivered_percent': round(delivered / total * 100) if total else 0,
        'open_exceptions': int(row['open_exceptions']),
    }
