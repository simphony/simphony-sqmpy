"""
    sqmpy.job.services
    ~~~~~

    Interface to job manager.
"""
from sqmpy.core import core_services
from sqmpy.job.constants import JOB_MANAGER

__author__ = 'Mehdi Sadeghi'


def list_jobs(page=None):
    """
    List current jobs
    :param page: page number
    """
    return core_services.get_component(JOB_MANAGER).list_jobs(page=page)


def submit_job(job_name, resource_url, uploaded_files, **kwargs):
    """
    Submit a new job along with its input files. Input files will be moved under
        a new folder with this structure: <staging_dir>/<username>/<job_id>/input_files/
    :param name: job name
    :param resource_url: resource to submit job there
    :param uploaded_files: a list of <filename, file_stream, relation> for each given file.
    :param kwargs::
        :param total_cpu_count:
        :param spmd_variation:
        :param walltime_limit:
        :param adaptor: the backend to be used, should be 'shell' or 'sge'
        :param description: about the job
    :return: job id
    """
    return core_services.get_component(JOB_MANAGER).submit_job(job_name,
                                                               resource_url,
                                                               uploaded_files,
                                                               **kwargs)


def cancel_job(job_id):
    """
    Cancel a job
    :param job_id:
    :return:
    """
    return core_services.get_component(JOB_MANAGER).cancel_job(job_id)


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