"""
    sqmpy.manager
    ~~~~~

    Provides user management
"""
import ldap
import bcrypt
from flask import current_app, session

from .exceptions import SecurityManagerException
from .models import User

__author__ = 'Mehdi Sadeghi'


def validate_login(username, password):
    """
    Checks the login on the configured backend.
    """
    if current_app.config.get('USE_LDAP_LOGIN'):
        return _valid_ldap_login(username, password)
    else:
        return _valid_login(username, password)


def _valid_login(username, password):
    """
    Checks if the given password is valid for the username
    """
    user = User.query.filter_by(username=username).first()
    if user is not None:
        return _is_correct_password(password, user.password)

    return False


def _valid_ldap_login(username, password):
    """
    Tries to login using LDAP
    """
    if password in (None, ''):
        print ('No LDAP password is provided')
        return False
    user, dn, entry = _get_ldap_user(username)
    if __debug__:
        print 'Got ldap user: %s %s %s' % (user, dn, entry)

    try:
        if 'LDAP_SERVER' not in current_app.config:
            raise Exception('Missing LDAP server information.')

        ld = ldap.initialize('ldap://{host}:{port}'.format(
            host=current_app.config.get('LDAP_SERVER'),
            port=current_app.config.get('LDAP_PORT', 389)
        ))
        result = ld.simple_bind_s(dn, password)
        if __debug__:
            print 'LDAP bind_simple_s result is %s' % str(result)

        # Keep password for SSH job submission
        session['password'] = password
        return True
    except ldap.INVALID_CREDENTIALS:
        return False
    else:
        raise


def get_user(username):
    """
    Checks the login on the configured backend.
    """
    if current_app.config.get('USE_LDAP_LOGIN'):
        user, dn, entry = _get_ldap_user(username)
        return user
    else:
        return _get_user(username)


def _get_user(username):
    """
    Returns the user with given username
    :param username:
    :return:
    """
    user = User.query.filter_by(username=username).one()
    if user is None:
        raise SecurityManagerException(
            'User [{username}] not found.'.format(username=username))
    return user


def _get_ldap_user(username):
    """
    Returns an LDAP user
    :param username
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
    ldap_filter = '(&(objectclass=person)(uid=%s))' % username
    # A correct basedn is required for search in some setups. Should be finxed.
    # basedn = current_app.config.get('LDAP_BASEDN', '')
    results = ld.search_s('',
                          ldap.SCOPE_SUBTREE,
                          ldap_filter)
    if len(results) < 1:
        raise Exception('User %s not found' % username)
    dn, entry = results[0]
    if __debug__:
        print('Found dn %s for user %s' % (dn, username))
    email = None
    if len(entry['mail']) > 0:
        email = entry['mail'][0]
    user = User(username=username,
                email=email)
    user.id = entry['uid'][0]
    return user, dn, entry


def get_password_digest(password):
    """
    Generates password digest
    :param password:
    """
    # encode is required to avoid encoding exceptions
    return bcrypt.hashpw(password.encode('utf-8'),
                         bcrypt.gensalt())


def _is_correct_password(password, digest):
    """
    Checks if the given password corresponds to the given digest
    :param password:
    :param digest:
    """
    return bcrypt.hashpw(password.encode('utf-8'),
                         digest.encode('utf-8')) == digest
