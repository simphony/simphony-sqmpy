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