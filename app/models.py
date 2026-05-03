from .extensions import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
from .security import hash_password, verify_password


user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(300), nullable=False)
    active = db.Column(db.Boolean, default=True)
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(self.password_hash, password)

    def has_role(self, role_name):
        return any(r.name == role_name for r in self.roles)

    def has_permission(self, permission_name):
        for role in self.roles:
            for p in role.permissions:
                if p.name == permission_name:
                    return True
        return False

    def has_mapped_permission(self, resource, action):
        """Resolved name from Setting inventory.permission.* fallback; mirrors dynamic_permission decorator."""
        name = resolve_mapped_permission_name(resource, action)
        return bool(name and self.has_permission(name))

    @property
    def is_active(self):
        # Flask-Login uses `is_active` to determine whether the user is allowed to authenticate
        return bool(self.active)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    permissions = db.relationship('Permission', secondary=role_permissions, backref=db.backref('roles', lazy='dynamic'))


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(200), unique=True, nullable=False)
    value = db.Column(db.String(1000), nullable=True)


_MAPPED_PERM_FALLBACKS = {
    ('inventory', 'view'): 'inventory.view',
    ('inventory', 'add'): 'inventory.add',
    ('inventory', 'edit'): 'inventory.edit',
    ('inventory', 'delete'): 'inventory.delete',
}


def resolve_mapped_permission_name(resource: str, action: str) -> str:
    key = f"{resource}.permission.{action}"
    row = Setting.query.filter_by(key=key).first()
    val = row.value.strip() if row and row.value else ''
    return val if val else _MAPPED_PERM_FALLBACKS.get((resource, action), '')


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, default=0)
    def __repr__(self):
        return f"<Item {self.name} ({self.quantity})>"


class AnonymousUser(AnonymousUserMixin):
    def has_role(self, role_name):
        return False
    def has_permission(self, permission_name):
        return False
    def has_mapped_permission(self, resource, action):
        return False
