import pytest
from app import create_app
from app.extensions import db
from app.models import User, Role


@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        admin_role = Role(name='admin')
        user_role = Role(name='user')
        db.session.add_all([admin_role, user_role])
        db.session.commit()
        user = User(username='bob')
        user.set_password('Bobpass1!')
        user.roles.append(user_role)
        admin = User(username='super')
        admin.set_password('Superpass1!')
        admin.roles.append(admin_role)
        db.session.add_all([user, admin])
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password):
    return client.post('/login', data={'username':username,'password':password}, follow_redirects=True)


def test_admin_access_blocked_for_user(client):
    rv = login(client, 'bob', 'Bobpass1!')
    assert b'Logged in' in rv.data
    rv = client.get('/admin/')
    assert rv.status_code == 403


def test_admin_access_allowed_for_admin(client):
    rv = login(client, 'super', 'Superpass1!')
    assert b'Logged in' in rv.data
    rv = client.get('/admin/')
    assert b'Admin Dashboard' in rv.data
