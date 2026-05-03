import pytest
from app import create_app
from app.extensions import db
from app.models import User, Role


@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        role = Role(name='user')
        db.session.add(role)
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_register_and_login(client, app):
    strong_pw = 'Secret123!'
    rv = client.post('/register', data={'username':'alice','password': strong_pw}, follow_redirects=True)
    assert b'Registered' in rv.data
    rv = client.post('/login', data={'username':'alice','password': strong_pw}, follow_redirects=True)
    assert b'Logged in' in rv.data
    rv = client.get('/dashboard')
    assert b'Welcome' in rv.data
