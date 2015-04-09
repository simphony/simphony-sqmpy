"""
    sqmpy.security
    ~~~~~~~~~~~~~~~~

    User management package
"""
from flask import Blueprint
from flask.ext.login import LoginManager

from ..core import core_services
from .models import User
from .manager import SecurityManager

__author__ = 'Mehdi Sadeghi'


# Create security blueprint
security_blueprint = Blueprint('sqmpy.security', __name__, url_prefix='/security')

@security_blueprint.record_once
def on_load(state):
    #Activate Login
    login_manager = LoginManager()
    login_manager.init_app(state.app)
    login_manager.login_view = '/security/login'

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)

#Register the component in core
core_services.register(SecurityManager())