import os
import sys

# Ensure project root is on sys.path when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import Role, Permission, User, Item
from sqlalchemy import inspect, text

app = create_app()


def seed():
    with app.app_context():
        # ensure all tables exist (will not alter existing tables)
        db.create_all()

        # simple migration: add `active` column to `user` table if missing
        inspector = inspect(db.engine)
        if 'user' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('user')]
            if 'active' not in cols:
                try:
                    db.session.execute(text('ALTER TABLE user ADD COLUMN active BOOLEAN DEFAULT 1'))
                    db.session.commit()
                    # backfill existing rows to active=1 where NULL
                    db.session.execute(text("UPDATE user SET active = 1 WHERE active IS NULL"))
                    db.session.commit()
                    print("Migrated: added 'active' column to user table")
                except Exception as e:
                    db.session.rollback()
                    print('Migration warning: could not add active column:', e)
        # create permissions
        p_view = Permission.query.filter_by(name='inventory.view').first()
        if not p_view:
            p_view = Permission(name='inventory.view')
        p_edit = Permission.query.filter_by(name='inventory.edit').first()
        if not p_edit:
            p_edit = Permission(name='inventory.edit')
        p_add = Permission.query.filter_by(name='inventory.add').first()
        if not p_add:
            p_add = Permission(name='inventory.add')
        p_delete = Permission.query.filter_by(name='inventory.delete').first()
        if not p_delete:
            p_delete = Permission(name='inventory.delete')

        # create roles
        admin_role = Role.query.filter_by(name='admin').first() or Role(name='admin')
        user_role = Role.query.filter_by(name='user').first() or Role(name='user')
        viewer_role = Role.query.filter_by(name='viewer').first() or Role(name='viewer')
        editor_role = Role.query.filter_by(name='editor').first() or Role(name='editor')

        # assign permissions to roles
        if p_view not in viewer_role.permissions:
            viewer_role.permissions.append(p_view)
        if p_view not in editor_role.permissions:
            editor_role.permissions.append(p_view)
        if p_edit not in editor_role.permissions:
            editor_role.permissions.append(p_edit)
        if p_add not in editor_role.permissions:
            editor_role.permissions.append(p_add)
        if p_view not in admin_role.permissions:
            admin_role.permissions.append(p_view)
        if p_edit not in admin_role.permissions:
            admin_role.permissions.append(p_edit)
        if p_add not in admin_role.permissions:
            admin_role.permissions.append(p_add)
        if p_delete not in admin_role.permissions:
            admin_role.permissions.append(p_delete)

        db.session.add_all([admin_role, user_role, viewer_role, editor_role, p_view, p_edit, p_add, p_delete])
        db.session.commit()

        # create seeded admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('adminpass')
            admin.roles.append(admin_role)
            db.session.add(admin)
            db.session.commit()
            print('Created admin user: username=admin password=adminpass')
        else:
            print('Admin user already exists')

        # create sample inventory items
        if not Item.query.first():
            items = [
                Item(name='Widget A', description='Small widget', quantity=10),
                Item(name='Widget B', description='Large widget', quantity=5),
            ]
            db.session.add_all(items)
            db.session.commit()
            print('Created sample inventory items')


if __name__ == '__main__':
    seed()
