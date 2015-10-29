"""
    sqmpy.security
    ~~~~~~~~~~~~~~~~

    User management package
"""
from flask import Blueprint
from flask.ext.login import LoginManager, AnonymousUserMixin

import manager

__author__ = 'Mehdi Sadeghi'


# Create security blueprint
security_blueprint = Blueprint('security', __name__, url_prefix='/security')


@security_blueprint.record_once
def on_load(state):
    # Activate Login
    login_manager = login_manager_factory(state)
    login_manager.init_app(state.app)


def login_manager_factory(state):
    """
    Create a login manager accordingly.
    """
    login_manager = LoginManager()
    login_manager.login_view = '/security/login'
    login_manager.login_message_category = "warning"

    # Set custom anonymous user to return the user which is running the
    #   process.
    def make_anon_user():
        return AnonymousUserMixin()
    login_manager.anonymous_user = make_anon_user

    if 'USE_LDAP_LOGIN' in state.app.config:
        @login_manager.user_loader
        def load_user(username):
            print('Going to load ldap user %s' % username)
            user, dn, entry = manager._get_ldap_user(username)
            return user
    else:
        @login_manager.user_loader
        def load_user(username):
            print('Going to load normal user %s' % username)
            return manager._get_user(username)

    return login_manager
