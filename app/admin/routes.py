from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from ..auth.decorators import roles_required
from ..extensions import db
from ..models import Role, Permission, User, Setting
from . import admin_bp


@admin_bp.before_request
def require_admin():
    # redirect unauthenticated users to login; forbid non-admins
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.path))
    if not current_user.has_role('admin'):
        abort(403)


@admin_bp.route('/')
@roles_required('admin')
def index():
    roles = Role.query.order_by(Role.name).all()
    users = User.query.order_by(User.username).all()
    perms = Permission.query.order_by(Permission.name).all()
    # load current inventory permission mappings
    mapping_keys = ['inventory.permission.view', 'inventory.permission.add', 'inventory.permission.edit', 'inventory.permission.delete']
    mappings = {k: (Setting.query.filter_by(key=k).first().value if Setting.query.filter_by(key=k).first() else '') for k in mapping_keys}
    return render_template('admin.html', roles=roles, users=users, perms=perms, mappings=mappings)


@admin_bp.route('/users/toggle_active', methods=['POST'])
@roles_required('admin')
def toggle_user_active():
    username = request.form.get('username')
    if not username:
        flash('Username required', 'warning')
        return redirect(url_for('admin.index'))
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'warning')
        return redirect(url_for('admin.index'))
    # prevent self-suspension
    if user.username == current_user.username:
        flash('You cannot suspend/unsuspend your own account.', 'warning')
        return redirect(url_for('admin.index'))
    user.active = not user.active
    db.session.commit()
    flash(('Unsuspended' if user.active else 'Suspended') + f' user {user.username}', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/delete', methods=['POST'])
@roles_required('admin')
def delete_user():
    username = request.form.get('username')
    if not username:
        flash('Username required', 'warning')
        return redirect(url_for('admin.index'))
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'warning')
        return redirect(url_for('admin.index'))
    if user.username == current_user.username:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.index'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} deleted', 'info')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/remove_role', methods=['POST'])
@roles_required('admin')
def remove_role_from_user():
    username = request.form.get('username')
    role_name = request.form.get('role_name')
    if not username or not role_name:
        flash('Username and role required', 'warning')
        return redirect(url_for('admin.index'))
    user = User.query.filter_by(username=username).first()
    role = Role.query.filter_by(name=role_name).first()
    if not user or not role:
        flash('User or role not found', 'warning')
        return redirect(url_for('admin.index'))
    if role in user.roles:
        user.roles.remove(role)
        db.session.commit()
        flash(f'Removed role {role.name} from {user.username}', 'success')
    else:
        flash('User does not have that role', 'info')
    return redirect(url_for('admin.index'))


@admin_bp.route('/roles/create', methods=['POST'])
@roles_required('admin')
def create_role():
    name = request.form.get('name')
    if not name:
        flash('Role name required', 'warning')
        return redirect(url_for('admin.index'))
    if Role.query.filter_by(name=name).first():
        flash('Role exists', 'warning')
        return redirect(url_for('admin.index'))
    role = Role(name=name)
    db.session.add(role)
    db.session.commit()
    flash('Role created', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/inventory/mapping', methods=['POST'])
@roles_required('admin')
def set_inventory_mapping():
    view_perm = request.form.get('view_perm')
    add_perm = request.form.get('add_perm')
    edit_perm = request.form.get('edit_perm')
    delete_perm = request.form.get('delete_perm')
    pairs = [('inventory.permission.view', view_perm), ('inventory.permission.add', add_perm), ('inventory.permission.edit', edit_perm), ('inventory.permission.delete', delete_perm)]
    for key, val in pairs:
        if not val:
            continue
        s = Setting.query.filter_by(key=key).first()
        if not s:
            s = Setting(key=key, value=val)
            db.session.add(s)
        else:
            s.value = val
    db.session.commit()
    flash('Inventory permission mapping updated', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/assign', methods=['POST'])
@roles_required('admin')
def assign_role():
    username = request.form.get('username')
    role_name = request.form.get('role')
    if not username or not role_name:
        flash('Username and role required', 'warning')
        return redirect(url_for('admin.index'))
    user = User.query.filter_by(username=username).first()
    role = Role.query.filter_by(name=role_name).first()
    if not user or not role:
        flash('User or role not found', 'warning')
        return redirect(url_for('admin.index'))
    if role not in user.roles:
        user.roles.append(role)
        db.session.commit()
        flash(f'Assigned role {role.name} to {user.username}', 'success')
    else:
        flash('User already has role', 'info')
    return redirect(url_for('admin.index'))


@admin_bp.route('/permissions/create', methods=['POST'])
@roles_required('admin')
def create_permission():
    name = request.form.get('perm_name')
    if not name:
        flash('Permission name required', 'warning')
        return redirect(url_for('admin.index'))
    if Permission.query.filter_by(name=name).first():
        flash('Permission exists', 'warning')
        return redirect(url_for('admin.index'))
    perm = Permission(name=name)
    db.session.add(perm)
    db.session.commit()
    flash('Permission created', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/roles/assign_permission', methods=['POST'])
@roles_required('admin')
def assign_permission():
    role_name = request.form.get('role_name')
    perm_name = request.form.get('perm_name')
    if not role_name or not perm_name:
        flash('Role and permission required', 'warning')
        return redirect(url_for('admin.index'))
    role = Role.query.filter_by(name=role_name).first()
    perm = Permission.query.filter_by(name=perm_name).first()
    if not role or not perm:
        flash('Role or permission not found', 'warning')
        return redirect(url_for('admin.index'))
    if perm not in role.permissions:
        role.permissions.append(perm)
        db.session.commit()
        flash(f'Assigned permission {perm.name} to role {role.name}', 'success')
    else:
        flash('Role already has permission', 'info')
    return redirect(url_for('admin.index'))
