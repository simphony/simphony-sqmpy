__author__ = 'Mehdi Sadeghi'


from sqmpy.core import core_services
from sqmpy.communication import CommunicationChannelFactory
from sqmpy.communication.constants import COMMUNICATION_MANAGER


def register_factory(factory):
    """
    registers a communication channel factory
    :param factory: should be instance of CommunicationChannelFactory class
    :rtype : CommunicationChannelFactory
    """
    assert isinstance(factory, CommunicationChannelFactory)
    return core_services.get_component(COMMUNICATION_MANAGER).register_factory(factory)
