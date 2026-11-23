"""
API tests (B2.1, B2.4, B2.5): call the endpoints through Flask's test client
and check status codes and JSON error messages.

These tests only use requests that are refused or answered BEFORE any
database query, so they pass without MySQL running. Tests that change data
belong in a separate suite run against a test database.

Run from the PROJECT ROOT with:
    python -m pytest tests/
"""

import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


class TestHealthAndRouting:
    def test_health_endpoint_returns_ok(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.get_json() == {'status': 'ok'}

    def test_unknown_api_url_returns_json_404(self, client):
        response = client.get('/api/does-not-exist')
        assert response.status_code == 404
        assert response.is_json
        assert 'error' in response.get_json()

    def test_unknown_page_returns_friendly_404_without_a_stack_trace(self, client):
        response = client.get('/no-such-page')
        assert response.status_code == 404
        assert b'Traceback' not in response.data

    def test_wrong_method_returns_json_405(self, client):
        response = client.delete('/api/health')
        assert response.status_code == 405
        assert 'error' in response.get_json()


class TestCreateMedicineValidation:
    def test_body_that_is_not_json_returns_400(self, client):
        response = client.post('/api/medicines', data='not json', content_type='text/plain')
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_invalid_medicine_returns_400_with_field_messages(self, client):
        response = client.post('/api/medicines', json={'name': '', 'category': 'sweets'})
        assert response.status_code == 400
        body = response.get_json()
        assert 'name' in body['fields']
        assert 'category' in body['fields']


class TestListValidation:
    @pytest.mark.parametrize('query', ['page=0', 'page=abc', 'size=0', 'size=1000', 'size=-3'])
    def test_bad_paging_values_return_400(self, client, query):
        response = client.get(f'/api/medicines?{query}')
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_unknown_category_filter_returns_400(self, client):
        response = client.get('/api/medicines?category=sweets')
        assert response.status_code == 400

    def test_unknown_stock_status_filter_returns_400(self, client):
        response = client.get('/api/medicines?status=Fantastic')
        assert response.status_code == 400
