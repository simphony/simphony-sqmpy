"""
    sqmpy.manager
    ~~~~~

    Provides user management
"""
import bcrypt

from sqmpy.core import SQMComponent
from sqmpy.security.constants import SECURITY_MANAGER
from sqmpy.security.models import User

__author__ = 'Mehdi Sadeghi'


class SecurityManager(SQMComponent):
    """
    Class to deal with security and users in SQM
    """
    def __init__(self):
        super(SecurityManager, self).__init__(SECURITY_MANAGER)

    def valid_login(self, email, password):
        """
        Checks if the given password is valid for the username
        """
        user = User.query.filter_by(email=email).first()
        if user is not None:
            return _is_correct_password(password, user.password)

        return False


def get_password_digest(password):
    """
    Generates password digest
    :param password:
    """
    return bcrypt.hashpw(password, bcrypt.gensalt())


def _is_correct_password(password, digest):
    """
    Checks if the given password corresponds to the given digest
    :param password:
    :param digest:
    """
    return bcrypt.hashpw(password, digest) == digest