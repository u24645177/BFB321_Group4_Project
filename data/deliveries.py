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

