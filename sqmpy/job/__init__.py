"""
    sqmpy.job
    ~~~~~~~~~~~~~~~~

    Provides job submission and monitoring.
"""
from flask import Blueprint

from .manager import JobManager

__author__ = 'Mehdi Sadeghi'


job_blueprint = Blueprint('sqmpy.job', __name__)

@job_blueprint.context_processor
def job_cnx_processor():
    return dict(active_page='job')