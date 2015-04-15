"""
    sqmpy.job
    ~~~~~~~~~

    Provides job submission and monitoring.
"""
from flask import Blueprint, g

__author__ = 'Mehdi Sadeghi'

job_blueprint = Blueprint('job', __name__, url_prefix='/jobs')

@job_blueprint.context_processor
def job_cnx_processor():
    return dict(active_page=job_blueprint.name)


@job_blueprint.before_request
def add_job_list(*args, **kwargs):
    g.__jobs = {}