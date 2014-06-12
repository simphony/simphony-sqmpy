from sqmpy.core import core_services
from sqmpy.security.constants import SECURITY_MANAGER

__author__ = 'Mehdi Sadeghi'


def valid_login(email, password):
    """
    Checks if the login is valid
    """
    print "In valid login method"
    return core_services.get_component(SECURITY_MANAGER).valid_login(email,
                                                                     password)