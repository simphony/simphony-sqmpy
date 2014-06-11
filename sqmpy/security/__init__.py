__author__ = 'Mehdi Sadeghi'

from flask.ext.login import LoginManager

from sqmpy import app
from sqmpy.security.models import User


#Activate Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """
    This method will load requested user or return None
    """
    return User.query.get(user_id)