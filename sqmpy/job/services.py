"""
    sqmpy.job.services
    ~~~~~

    Interface to job manager.
"""
from sqmpy.core import core_services
from sqmpy.job.constants import JOB_MANAGER

__author__ = 'Mehdi Sadeghi'


def list_jobs():
    """
    List current jobs
    """
    return core_services.get_component(JOB_MANAGER).list_jobs()


def submit_job(name, resource, script, inputfile=None, description=None, **kwargs):
    """
    Submit a new job
    :name: job name
    :resource: resource to submit job there
    :script: user script
    :inputfile: input data file if any
    :descritpion: about the job
    :return: job id
    """
    return core_services.get_component(JOB_MANAGER).submit_job(name, resource, script, inputfile, description, **kwargs)