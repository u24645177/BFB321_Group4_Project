"""
Users: checking a sign-in against the `users` table.

Passwords are never stored or compared in plain text: the table holds a
Werkzeug hash, and check_password_hash() compares the typed password with it.
"""

from werkzeug.security import check_password_hash

from db import fetch_one

ROLE_LABELS = {
    'admin': 'Admin',
    'procurement_officer': 'Procurement officer',
    'pharmacist': 'Pharmacist',
}


def authenticate(email, password):
    """
    Return the signed-in user's details if the email and password match an
    active user, otherwise None. The same None is returned for a wrong email
    and a wrong password, so the page never reveals which accounts exist.
    """
    email = (email or '').strip().lower()
    if not email or not password:
        return None
    user = fetch_one(
        """
        SELECT u.user_id, u.full_name, u.email, u.password_hash, u.role, f.name AS facility
        FROM users u
        LEFT JOIN facilities f ON f.facility_id = u.facility_id
        WHERE u.email = %s AND u.is_active = TRUE
        """,
        (email,),
    )
    if user is None or not check_password_hash(user['password_hash'], password):
        return None
    return {
        'id': user['user_id'],
        'name': user['full_name'],
        'email': user['email'],
        'role': user['role'],
        'role_label': ROLE_LABELS.get(user['role'], user['role']),
        'facility': user['facility'],
    }
