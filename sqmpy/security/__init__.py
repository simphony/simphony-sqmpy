"""
    sqmpy.security
    ~~~~~~~~~~~~~~~~

    User management package
"""
from flask import Blueprint
from flask.ext.login import LoginManager

from .models import User

__author__ = 'Mehdi Sadeghi'


# Create security blueprint
security_blueprint = Blueprint('security', __name__, url_prefix='/security')

@security_blueprint.record_once
def on_load(state):
    # Activate Login
    login_manager = LoginManager()
    login_manager.init_app(state.app)
    login_manager.login_view = '/security/login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)