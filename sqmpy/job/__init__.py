"""
    sqmpy.job
    ~~~~~~~~~~~~~~~~

    Provides job submission and monitoring.
"""
from flask import Blueprint

from sqmpy.job.manager import JobManager

__author__ = 'Mehdi Sadeghi'

job_blueprint = Blueprint('sqmpy.job', __name__)