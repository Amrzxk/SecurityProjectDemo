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
        admin = User(username='admin')
        admin.set_password('Adminpass1!')
        admin.roles.append(admin_role)
        victim = User(username='victim')
        victim.set_password('Victimpass1!')
        victim.roles.append(user_role)
        db.session.add_all([admin, victim])
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_admin_can_suspend_user(client):
    # login as admin
    rv = login(client, 'admin', 'Adminpass1!')
    assert b'Logged in' in rv.data
    # suspend victim
    rv = client.post('/admin/users/toggle_active', data={'username': 'victim'}, follow_redirects=True)
    assert b'Suspended' in rv.data or b'Unsuspended' in rv.data
    # logout
    client.get('/logout')
    # victim cannot login
    rv = login(client, 'victim', 'Victimpass1!')
    assert b'Account suspended' in rv.data
