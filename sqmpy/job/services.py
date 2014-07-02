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


def submit_job(name, resource_id, script, input_files=None, description=None, **kwargs):
    """
    Submit a new job along with its input files. Input files will be moved under
        a new folder with this structure: <staging_dir>/<username>/<job_id>/input_files/
    :name: job name
    :resource_id: resource to submit job there
    :script: user script
    :input_files: a list of <filename, file_stream> for each given file.
    :description: about the job
    :return: job id
    """
    return core_services.get_component(JOB_MANAGER).submit_job(name, resource_id, script, input_files, description, **kwargs)


def get_job(job_id, *args, **kwargs):
    """
    Get a job
    :job_id: name of the job
    """
    return core_services.get_component(JOB_MANAGER).get_job(job_id, *args, **kwargs)


def get_file_location(job_id, file_name):
    """
    Returns the folder of the file
    :param job_id:
    :param file_name:
    :return:
    """
    return core_services.get_component(JOB_MANAGER).get_file_location(job_id, file_name)