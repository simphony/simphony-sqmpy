__author__ = 'Mehdi Sadeghi'

from sqmpy.core import SQMComponent, SQMException
from sqmpy.core import core_services
from sqmpy.communication.constants import COMMUNICATION_MANAGER


class ChannelManagerException(SQMException):
    """
    Represents different exceptions related to channel manager
    """


class CommunicationChannelFactory(object):
    """
    A factory to be overriden by channel implementations
    """
    def __init__(self, name):
        """
        :param name: name of the factory
        """
        self._name = name

    def create_channel(self, name):
        """
        Creates a channel instance.
        """
        raise NotImplementedError

    def get_name(self):
        """
        Get factory name.
        """
        return self._name


class CommunicationChannel(object):
    """
    Representing communication channel base class
    """
    def connect(self, hostname, username):
        """
        Connects to remote host
        :param hostname: hostname
        :param username: username
        """
        raise NotImplementedError

    def exec_command(self, command, *args, **kwargs):
        """
        Run a command on remote host
        :param command: executable name
        :param args: this should contain direct parameters of the remote program
        :param kwargs: this should contain named parameters of the remote program
        """
        raise NotImplementedError


class CommunicationManager(SQMComponent):
    """
    Controller class for communication channels
    """

    def __init__(self):
        super(CommunicationManager, self).__init__(COMMUNICATION_MANAGER)
        self._factories = {}

    def register_factory(self, factory):
        """
        Add a channel
        :param factory: object of type ChannelBase
        """
        assert isinstance(factory, CommunicationChannelFactory)
        self._factories[factory.get_name()] = factory

    def get_channel(self, name):
        """
        Get the channel object
        :param name: name of the channel
        """

        if name in self._factories:
            return self._factories[name].create_channel()
        else:
            raise ChannelManagerException('Requested channel does not exists: %s' % name)


#Register the component in core
#@TODO: This should be dynamic later
core_services.register(CommunicationManager())