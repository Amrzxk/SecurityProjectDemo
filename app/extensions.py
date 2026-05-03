from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


db = SQLAlchemy()
login_manager = LoginManager()
# Rate limiter (defaults to in-memory storage for the demo)
limiter = Limiter(key_func=get_remote_address)
