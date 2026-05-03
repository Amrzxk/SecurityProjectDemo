from flask import Flask
from sqlalchemy import inspect, text
from .extensions import db, login_manager, limiter


def _ensure_item_sensitive_note_column():
    """SQLite: add sensitive_note_cipher if DB predates column (after db.create_all)."""
    inspector = inspect(db.engine)
    if 'item' not in inspector.get_table_names():
        return
    cols = {c['name'] for c in inspector.get_columns('item')}
    if 'sensitive_note_cipher' not in cols:
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE item ADD COLUMN sensitive_note_cipher TEXT'))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    # initialize rate limiter
    limiter.init_app(app)
    # use a custom anonymous user so templates can call has_role / has_permission safely
    from .models import AnonymousUser
    login_manager.anonymous_user = AnonymousUser
    login_manager.login_view = 'auth.login'

    # register blueprints
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .admin.routes import admin_bp
    from .inventory.routes import inventory_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(inventory_bp)

    with app.app_context():
        db.create_all()
        _ensure_item_sensitive_note_column()

    return app
