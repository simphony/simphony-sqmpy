"""
    sqmpy.manager
    ~~~~~

    Provides user management
"""
import flask.ext.login as flask_login
from flask import current_app, session, request, g

from . import constants
from .models import User
from .exceptions import SecurityManagerException
from ..database import db

LDAP_AVAILABLE=True
try:
    import ldap
except:
    LDAP_AVAILABLE=False

__author__ = 'Mehdi Sadeghi'


def login_user(username, password):
    """
    Login in the given user.
    """
    if current_app.config.get('USE_LDAP_LOGIN'):
        if not LDAP_AVAILABLE:
            # If python-ldap is not installed raise an error
            raise SecurityManagerException('Error loading ldap package.')
        return _login_ldap_user(username, password)
    elif _is_valid_login(username, password):
        user = User.query.filter_by(username=username).one()
        flask_login.login_user(user, remember=request.form.get('remember'))
        return True
    # If non of above is the case
    return False


def get_user(user_id):
    """
    Returns the user with given username
    :param user_id:
    :return:
    """
    user = User.query.get(user_id)
    if user is None:
        raise SecurityManagerException(
            'User [{user_id}] not found.'.format(user_id=user_id))
    return user


def _is_valid_login(username, password):
    """
    Checks if the given password is valid for the username
    """
    user = User.query.filter_by(username=username).first()
    if user is not None:
        return user.is_equal_password(password)

    return False


def _login_ldap_user(username, password):
    """
    Tries to login using LDAP
    """
    if password in (None, ''):
        print ('No LDAP password is provided')
        return False

    # Get Ldap info about user
    dn, entry = _get_ldap_user(username)
    email = None
    if len(entry['mail']) > 0:
        email = entry['mail'][0]

    if 'cn' in entry:
        g.fullname = entry['cn'][0]

    if 'cn' in entry:
        session['fullname'] = entry['cn'][0]

    try:
        if 'LDAP_SERVER' not in current_app.config:
            raise Exception('Missing LDAP server information.')

        ld = ldap.initialize('ldap://{host}:{port}'.format(
            host=current_app.config.get('LDAP_SERVER'),
            port=current_app.config.get('LDAP_PORT', 389)
        ))
        # Everything in Flask is Unicode but it seems that python-ldap library
        # does not play well with Unicode objects and throws nicodeEncodeError.
        # Therefore we convert it to bytes and pass it to ldap-python.
        ld.simple_bind_s(dn, password.encode('utf-8'))

        # Check if the ldap user exists in local database
        local_user =\
            User.query.filter(User.username == username,
                              User.origin ==
                              constants.UserOrigin.ldap.value).first()
        if not local_user:
            # Add a track record for ldap user
            local_user = User(username=username,
                              email=email)
            local_user.origin = constants.UserOrigin.ldap.value
            db.session.add(local_user)
            db.session.commit()
        # Finally ask flask_login to log in the user
        flask_login.login_user(local_user,
                               remember=request.form.get('remember'))
        return True
    except ldap.INVALID_CREDENTIALS:
        return False


def _get_ldap_user(user_id):
    """
    Returns an LDAP user
    :param user_id
    :return:
    """
    if 'LDAP_SERVER' not in current_app.config:
        raise Exception('Missing LDAP server information.')

    ld = ldap.initialize('ldap://{host}:{port}'.format(
        host=current_app.config.get('LDAP_SERVER'),
        port=current_app.config.get('LDAP_PORT', 389)
    ))

    # TODO: The current LDAP support is very limited. This should be fixed for
    # a proper support.
    # So far only anonymous LDAP is supported
    # ld.simple_bind_s()
    ldap_filter = '(&(objectclass=person)(uid=%s))' % user_id
    # A correct basedn is required for search in some setups. Should be finxed.
    # basedn = current_app.config.get('LDAP_BASEDN', '')
    results = ld.search_s('',
                          ldap.SCOPE_SUBTREE,
                          ldap_filter)
    if len(results) < 1:
        raise Exception('LDAP error: user %s not found' % user_id)

    dn, entry = results[0]
    if __debug__:
        print('Found dn %s for user %s' % (dn, user_id))

    return dn, entry
