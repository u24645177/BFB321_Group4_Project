"""
Sign-in with the seeded test accounts (Step 4).

After a correct email and password, the user's id, name and role are kept in
Flask's signed session cookie until they sign out, and every page shows who
is signed in.

Prototype scope: sign-in identifies the user but does not restrict access
yet. Pages and the API work without signing in, and the role stored for each
user is not yet used to limit what they can do. Enforcing sign-in and
role-based permissions is the planned next step.
"""

from flask import (Blueprint, current_app, g, redirect, render_template, request,
                   session, url_for)

from data import users

auth_bp = Blueprint('auth', __name__)


def _safe_next(target):
    """Only follow a ?next= link back into this site (never to another site)."""
    if target and target.startswith('/') and not target.startswith('//'):
        return target
    return url_for('pages.index')


@auth_bp.before_app_request
def load_user():
    """Runs before every request: remember who is signed in (None if nobody)."""
    g.user = session.get('user')


@auth_bp.app_context_processor
def inject_user():
    """Make the signed-in user available to every template as current_user."""
    return {'current_user': g.get('user')}


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Show the sign-in form, and sign the user in when the details are correct."""
    if g.get('user'):
        return redirect(url_for('pages.index'))

    error, email = None, ''
    if request.method == 'POST':
        email = request.form.get('email', '')
        user = users.authenticate(email, request.form.get('password', ''))
        if user is None:
            error = 'That email and password do not match an active account.'
            current_app.logger.warning('Failed sign-in for %s', email.strip().lower())
        else:
            session.clear()
            session['user'] = user
            current_app.logger.info('%s signed in as %s', user['email'], user['role'])
            return redirect(_safe_next(request.args.get('next')))

    return render_template('login.html', error=error, email=email), (401 if error else 200)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Sign out and go back to the sign-in page."""
    session.clear()
    return redirect(url_for('auth.login'))
