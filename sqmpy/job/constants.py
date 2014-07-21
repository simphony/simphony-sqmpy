"""
    sqmpy.job.constants
    ~~~~~~~~~~~~~~~~

    Constants to be used in job package
"""
from enum import Enum, unique

import saga

__author__ = 'Mehdi Sadeghi'

JOB_MANAGER = 'sqmpy.job.manager'


#TODO Could be replaced with Enum class in python 3.4 (is back ported)
class JobStatus(object):
    """
    Represents job states
    """
    INIT = 'Initialization'
    UNKNOWN = saga.job.UNKNOWN
    NEW = saga.job.NEW
    PENDING = saga.job.PENDING
    RUNNING = saga.job.RUNNING
    DONE = saga.job.DONE
    CANCELED = saga.job.CANCELED
    FAILED = saga.job.FAILED
    SUSPENDED = saga.job.SUSPENDED


@unique
class FileRelation(Enum):
    """
    Relation between job and file
    """
    input = 0
    output = 1
    error = 2
    script = 3

