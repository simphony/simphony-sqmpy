__author__ = 'Mehdi Sadeghi'


class ChannelControllerException(Exception):
    """
    Represents different exceptions related to channel manager
    """

class ChannelBase:
    """
    Representing communication channel base class
    """

    def __init__(self, name):
        """
        @name: name of the channel to be registered with
        """
        self._name = name

    def get_name(self):
        """
        Get name of the channel
        """
        return self._name

    def connect(self, hostname, username):
        """
        Connects to remote host
        @hostname: hostname
        @username: username
        """
        raise NotImplementedError

    def exec_command(self, command, *args, **kwargs):
        """
        Run a command on remote host
        @command: executable name
        @args: this should contain direct parameters of the remote program
        @kwargs: this should contain named parameters of the remote program
        """
        raise NotImplementedError


class ChannelController:
    """
    Controller class for communication channels
    """

    def __init__(self):
        self._channels = {}
    
    def get_channel(self, name):
        """
        Get the channel object
        @name: name of the channel
        """

        if name in self._channels:
            return self._channels[name]
        else:
            raise ChannelControllerException('Requested channel does not exists: %s' % name)