"""Inventory UI respects mapped permissions independently (e.g. delete without edit)."""
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Role, Permission, Item


@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()

        pv = Permission(name='inventory.view')
        pd = Permission(name='inventory.delete')
        viewer = Role(name='viewer')
        deleter = Role(name='deleteonly')
        viewer.permissions.append(pv)
        deleter.permissions.append(pd)

        u = User(username='zak_like')
        u.set_password('ZakPass1!')
        u.roles.extend([viewer, deleter])

        db.session.add_all([viewer, deleter, u, pv, pd])
        db.session.flush()
        db.session.add(Item(name='Thing', description='test', quantity=1))
        db.session.commit()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, username='zak_like', password='ZakPass1!'):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_inventory_list_delete_without_edit_buttons(client):
    assert _login(client).status_code == 200
    rv = client.get('/inventory/')
    assert rv.status_code == 200
    body = rv.get_data(as_text=True)
    assert 'Delete' in body
    assert '>Edit<' not in body


def test_delete_only_user_can_delete_item(app, client):
    assert _login(client).status_code == 200
    with app.app_context():
        item_id = Item.query.filter_by(name='Thing').first().id
    rv = client.post(f'/inventory/{item_id}/delete', follow_redirects=True)
    assert rv.status_code == 200
    with app.app_context():
        assert Item.query.filter_by(name='Thing').first() is None


def test_resolve_mapped_fallback_matches_dynamic_permission(app):
    with app.app_context():
        from app.models import resolve_mapped_permission_name
        assert resolve_mapped_permission_name('inventory', 'delete') == 'inventory.delete'

