from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_user, logout_user, login_required
from ..extensions import db, limiter
from flask_limiter.util import get_remote_address
from ..models import User, Role
import re


def is_strong_password(password: str):
    if not password or len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must include a lowercase letter.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must include an uppercase letter.'
    if not re.search(r'\d', password):
        return False, 'Password must include a digit.'
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, 'Password must include a symbol (e.g. !@#$%).'
    return True, None


# def _login_user_key():
#     # Rate limit key by username when available, otherwise by remote addr
#     username = (request.form.get('username') or '').strip()
#     if username:
#         return f'user:{username}'
#     return get_remote_address()

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password:
            flash('Username and password required', 'warning')
            return redirect(url_for('auth.register'))
        # password strength
        ok, msg = is_strong_password(password)
        if not ok:
            flash(msg, 'warning')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(username=username).first():
            flash('User already exists', 'warning')
            return redirect(url_for('auth.register'))
        user = User(username=username, email=email)
        user.set_password(password)
        role = Role.query.filter_by(name='user').first()
        if role:
            user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        flash('Registered. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
# @limiter.limit('10 per minute')
# @limiter.limit('5 per hour', key_func=_login_user_key)
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            if not user.is_active:
                flash('Account suspended. Contact the administrator.', 'danger')
                return render_template('login.html')
            if user.check_password(password):
                login_user(user)
                flash('Logged in successfully', 'success')
                return redirect(url_for('main.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You are logged out', 'info')
    return redirect(url_for('main.index'))
