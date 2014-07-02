"""
    sqmpy.exceptions
    ~~~~~

    Contains job management exceptions
"""
__author__ = 'Mehdi Sadeghi'


class JobManagerException(Exception):
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