"""
    sqmpy.exceptions
    ~~~~~

    Contains job management exceptions
"""
from ..exceptions import SqmpyException

__author__ = 'Mehdi Sadeghi'


class JobManagerException(SqmpyException):
    """
    Represents job manager exceptions
    """


class JobNotFoundException(JobManagerException):
    """
    When requested job does not exist.
    """

class FileNotFoundException(JobManagerException):
    """
    When requested file does not exist.
    """