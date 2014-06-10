__author__ = 'Mehdi Sadeghi'

from ssh import SSHClient

from sqmpy.communication.controller import ChannelBase


class SSHChannel(ChannelBase):
    """
    Representing a SSH channel to communicate with
    """

    def __init__(self):
        self.client = SSHClient()
        self.client.load_system_host_keys()
        super(self, 'SSH')

    def connect(self, hostname, username):
        """
        Connects to remote host
        @hostname: hostname
        @username: username
        """
        self.client.connect(hostname, username=username)

    def exec_command(self, command, *args, **kwargs):
        """
        Run a command on remote host
        @command: executable name
        @args: this should contain direct parameters of the remote program
        @kwargs: this should contain named parameters of the remote program
        """