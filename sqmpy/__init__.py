"""
    sqmpy
    ~~~~~

    A job management web application that makes it easier
    for scientists to submit and monitor jobs to remote
    to remote resources.
    `sqm' stands for Simple Queue Manager.
"""
from rq import Queue
from rq.job import Job
from worker import conn

__author__ = 'Mehdi Sadeghi'
__version__ = 'v0.2'

q = Queue(connection=conn)
