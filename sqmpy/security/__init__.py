"""
    sqmpy.security
    ~~~~~~~~~~~~~~~~

    User management package
"""
from flask import Blueprint
from flask.ext.login import LoginManager, AnonymousUserMixin

from .models import User

__author__ = 'Mehdi Sadeghi'


# Create security blueprint
security_blueprint = Blueprint('security', __name__, url_prefix='/security')


# This does not look good but there is justification for it. Since we use saga and
# saga uses ssh to connect to remote hosts and we do not ask users for their ssh
# credentials, therefore we use the ssh keys which are available in home folder of
# the user which is running Sqmpy process. Therefore, no matter who is in front of
# the browser, we have will run commands on remote machines with the user who has
# run the Flask application in the first place.
class AnonymousOperator(AnonymousUserMixin):
    def __init__(self):
        super(AnonymousOperator, self).__init__()
        import getpass
        self.username = getpass.getuser()


@security_blueprint.record_once
def on_load(state):
    # Activate Login
    login_manager = LoginManager()
    login_manager.init_app(state.app)
    login_manager.login_view = '/security/login'

    # Set custom anonymous user to return the user which is running the process.
    def make_anon_user():
        return AnonymousOperator()
    login_manager.anonymous_user = make_anon_user

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)


