from flask import Flask
from .extensions import db, login_manager, limiter


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

    return app
