"""
Sign-in tests (Step 4).

Checking a password needs the database, so the user lookup is replaced with
the seeded test users (same emails and password as database/seed.sql).
"""

import pytest
from werkzeug.security import generate_password_hash

from app import app
from data import users

PASSWORD = 'MedSync2026!'
TEST_USERS = {
    'admin@medsync.test': ('Thandi Mokoena', 'admin'),
    'procurement@medsync.test': ('Pieter van der Merwe', 'procurement_officer'),
    'pharmacist@medsync.test': ('Lerato Nkosi', 'pharmacist'),
}
HASH = generate_password_hash(PASSWORD)


def fake_fetch_one(sql, params=()):
    email = params[0]
    if email not in TEST_USERS:
        return None
    name, role = TEST_USERS[email]
    return {'user_id': 1, 'full_name': name, 'email': email, 'password_hash': HASH,
            'role': role, 'facility': None}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(users, 'fetch_one', fake_fetch_one)
    return app.test_client()


def sign_in(client, email, password=PASSWORD):
    return client.post('/login', data={'email': email, 'password': password})


class TestSignIn:

    def test_sign_in_page_loads(self, client):
        assert client.get('/login').status_code == 200

    def test_wrong_password_is_refused(self, client):
        response = sign_in(client, 'admin@medsync.test', 'wrong-password')
        assert response.status_code == 401
        assert b'do not match' in response.data

    def test_unknown_email_gets_the_same_message(self, client):
        response = sign_in(client, 'nobody@medsync.test')
        assert response.status_code == 401
        assert b'do not match' in response.data

    def test_email_is_not_case_sensitive(self, client):
        assert sign_in(client, 'Admin@MedSync.test').status_code == 302

    def test_correct_details_sign_in_and_redirect(self, client):
        response = sign_in(client, 'pharmacist@medsync.test')
        assert response.status_code == 302
        with client.session_transaction() as session:
            assert session['user']['role'] == 'pharmacist'
            assert session['user']['role_label'] == 'Pharmacist'

    def test_next_link_cannot_leave_the_site(self, client):
        response = client.post('/login?next=//evil.example',
                               data={'email': 'admin@medsync.test', 'password': PASSWORD})
        assert response.headers['Location'] == '/'

    def test_sign_out_clears_the_session(self, client):
        sign_in(client, 'admin@medsync.test')
        client.post('/logout')
        with client.session_transaction() as session:
            assert 'user' not in session
