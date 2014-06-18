__author__ = 'Mehdi Sadeghi'

import ssh

from sqmpy.communication import CommunicationChannel, CommunicationChannelFactory
from sqmpy.communication.constants import SSH_CHANNEL


class SSHChannel(CommunicationChannel):
    """
    Representing a SSH channel to communicate with
    """
    def __init__(self):
        self.client = ssh.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(ssh.AutoAddPolicy())
        super(SSHChannel, self).__init__()

    def connect(self, hostname, username=None):
        """
        Connects to remote host
        :param hostname: hostname
        :param username: username
        """
        self.client.connect(hostname, username=username)

    def exec_command(self, command, *args, **kwargs):
        """
        Run a command on remote host
        :param command: executable name
        :param args: this should contain direct parameters of the remote program
        :param kwargs: this should contain named parameters of the remote program
        """


class SSHFactory(CommunicationChannelFactory):
    """
    Creates SSH channels
    """
    def __init__(self):
        super(SSHFactory, self).__init__(SSH_CHANNEL)

    def create_channel(self):
        """
        Creates a SSH channel instance
        """
        return SSHChannel()