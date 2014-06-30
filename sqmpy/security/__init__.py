"""
    sqmpy.security
    ~~~~~~~~~~~~~~~~

    User management package
"""
from flask import Blueprint
from flask.ext.login import LoginManager

from sqmpy.core import core_services
from sqmpy.security.manager import SecurityManager
from sqmpy.security.models import User

__author__ = 'Mehdi Sadeghi'


#Activate Login
login_manager = LoginManager()

# Create security blueprint
security_blueprint = Blueprint('sqmpy.security', __name__)

@security_blueprint.record_once
def on_load(state):
    login_manager.init_app(state.app)
    login_manager.login_view = '/security/login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


#Register the component in core
#@TODO: This should be dynamic later
core_services.register(SecurityManager())