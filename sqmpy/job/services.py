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


def submit_job(name, resource_url, script, script_type, input_files=None, description=None, **kwargs):
    """
    Submit a new job along with its input files. Input files will be moved under
        a new folder with this structure: <staging_dir>/<username>/<job_id>/input_files/
    :param name: job name
    :param resource_url: resource to submit job there
    :param script: user script
    :param script_type: integer type of the script according to ScriptType enum
    :param input_files: a list of <filename, file_stream> for each given file.
    :param description: about the job
    :return: job id
    """
    return core_services.get_component(JOB_MANAGER).submit_job(name,
                                                               resource_url,
                                                               script,
                                                               script_type,
                                                               input_files,
                                                               description, **kwargs)


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