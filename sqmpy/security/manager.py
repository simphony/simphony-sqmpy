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
        return _is_valid_ldap_login(username, password)
    else:
        return _is_valid_login(username, password)


def _is_valid_login(username, password):
    """
    Checks if the given password is valid for the username
    """
    user = User.query.filter_by(username=username).first()
    if user is not None:
        return _is_correct_password(password, user.password)

    return False


def _is_valid_ldap_login(username, password):
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


def get_user_by_username(username):
    """
    Return a user based on username.
    """
    if current_app.config.get('USE_LDAP_LOGIN'):
        user, dn, entry = _get_ldap_user(username)
        return user
    else:
        return User.query.filter_by(username=username).one()


def get_user(user_id):
    """
    Checks the login on the configured backend.
    """
    if current_app.config.get('USE_LDAP_LOGIN'):
        user, dn, entry = _get_ldap_user(user_id)
        return user
    else:
        return _get_user(user_id)


def _get_user(user_id):
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
    email = None
    if len(entry['mail']) > 0:
        email = entry['mail'][0]
    if 'cn' in entry:
        from flask import g
        g.fullname = entry['cn'][0]
    user = User(username=user_id,
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
