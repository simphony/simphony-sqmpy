__author__ = 'Mehdi Sadeghi'

JOB_MANAGER = 'sqmpy.job.manager'


class JobStatus(object):
    """
    Represents job states
    """
    INIT = 'Initialization'
    QUEUED = 'Queued'
    RUNNING = 'Running'
    PAUSED = 'Paused'
    CANCELLED = 'Cancelled'
    FAILED = 'Failed'
    FINISHED = 'Finished'


class FileRelation(object):
    """
    Relation between job and file
    """
    INPUT = 0
    OUTPUT = 1
    ERROR = 2