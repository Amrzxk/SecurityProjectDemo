from functools import wraps
from flask import abort
from flask_login import current_user, login_required


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            for role in roles:
                if current_user.has_role(role):
                    return f(*args, **kwargs)
            abort(403)
        return wrapped
    return decorator


def permissions_required(*perms):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            for perm in perms:
                if current_user.has_permission(perm):
                    return f(*args, **kwargs)
            abort(403)
        return wrapped
    return decorator


def dynamic_permission(resource, action):
    """Check a permission name mapped for a resource/action.

    Admin can map e.g. key `inventory.permission.add` -> `inventory.addItem`.
    If no mapping exists, fall back to conventional permission names.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.has_mapped_permission(resource, action):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator
