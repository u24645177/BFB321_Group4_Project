"""
Database access: one MySQL connection per request, parameterised queries
and explicit transactions.

Settings come from the environment (.env), never from the code:
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

Usage in a route:
    from db import fetch_all, fetch_one, transaction

    rows = fetch_all("SELECT * FROM medicines WHERE category = %s", (category,))

    with transaction() as cur:          # commits on success, rolls back on error
        cur.execute("UPDATE inventory SET quantity_on_hand = %s WHERE inventory_id = %s", (qty, inv_id))

Always pass values as the second argument (%s placeholders). Never build SQL
by joining strings: PyMySQL escapes the parameters, which prevents SQL injection.
"""

import logging
import os
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from flask import current_app, g, has_app_context

load_dotenv()

logger = logging.getLogger(__name__)


def _setting(name, default=None):
    """Read a setting from the Flask config if available, otherwise from the environment."""
    if has_app_context() and name in current_app.config:
        return current_app.config[name]
    return os.getenv(name, default)


def _connect():
    """Open a new MySQL connection that returns rows as dictionaries."""
    return pymysql.connect(
        host=_setting('MYSQL_HOST', 'localhost'),
        port=int(_setting('MYSQL_PORT', 3306)),
        user=_setting('MYSQL_USER', 'root'),
        password=_setting('MYSQL_PASSWORD', ''),
        database=_setting('MYSQL_DATABASE', 'medsync'),
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=False,
    )


def get_db():
    """Return this request's connection, opening it on first use."""
    if 'db' not in g:
        g.db = _connect()
    return g.db


def close_db(exception=None):
    """Close the request's connection. Registered to run after every request."""
    conn = g.pop('db', None)
    if conn is not None:
        conn.close()


def init_app(app):
    """Register close_db so connections are always closed, even after an error."""
    app.teardown_appcontext(close_db)


def fetch_all(sql, params=()):
    """Run a SELECT and return every row as a list of dicts."""
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql, params=()):
    """Run a SELECT and return the first row as a dict, or None if there is no row."""
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


@contextmanager
def transaction():
    """
    Group writes so they succeed or fail together.

    Commits when the block finishes. If anything inside raises, every write
    in the block is rolled back, the failure is logged and the error is
    re-raised for the central error handlers to turn into a JSON response.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception('Database write failed and was rolled back')
        raise
