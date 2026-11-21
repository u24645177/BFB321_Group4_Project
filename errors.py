"""
Central error handlers. Every error is logged and the user gets a clean
message: JSON for /api URLs, a short page otherwise. No stack traces are
ever sent to the browser.
"""

import logging

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

FRIENDLY_MESSAGES = {
    400: 'The request was not valid.',
    404: 'That page or resource was not found.',
    405: 'That method is not allowed for this URL.',
    500: 'Something went wrong on our side. Please try again.',
}


def _error_response(status, message):
    """JSON for API calls, a simple HTML page for everything else."""
    if request.path.startswith('/api'):
        return jsonify({'error': message}), status
    page = f'<h1>Error {status}</h1><p>{message}</p><p><a href="/">Back to dashboard</a></p>'
    return page, status


def register_error_handlers(app):
    """Attach the handlers to the Flask app."""

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        status = error.code or 500
        log = logger.error if status >= 500 else logger.warning
        log('%s %s returned %s', request.method, request.path, status)
        return _error_response(status, FRIENDLY_MESSAGES.get(status, error.name))

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception('Unhandled error on %s %s', request.method, request.path)
        return _error_response(500, FRIENDLY_MESSAGES[500])