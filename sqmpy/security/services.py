from sqmpy.core import core_services
from sqmpy.security.constants import SECURITY_MANAGER

__author__ = 'Mehdi Sadeghi'


def valid_login(email, password):
    """
    Checks if the login is valid
    """
    return core_services.get_component(SECURITY_MANAGER).valid_login(email,
                                                                     password)

#
# def get_user(email):
#     """
#     Returns a user object
#     """
#     return core_services.get_component(SECURITY_MANAGER).get_user(email)