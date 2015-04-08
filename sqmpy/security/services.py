"""
    sqmpy.security.services
    ~~~~~

    Interface to security manager.
"""
from ..core import core_services
from .constants import SECURITY_MANAGER

__author__ = 'Mehdi Sadeghi'


def valid_login(email, password):
    """
    Checks if the login is valid
    """
    return core_services.get_component(SECURITY_MANAGER).valid_login(email,
                                                                     password)


def get_user(user_id):
    """
    Returns the user with given id
    :param id:
    :return:
    """
    return core_services.get_component(SECURITY_MANAGER).get_user(user_id)