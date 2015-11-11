"""
    sqmpy.job.manager
    ~~~~~

    Manager class along with it's helpers.
"""
from flask import current_app, g, abort
from flask.ext.login import current_user

import saga
from ..database import db
from .exceptions import JobManagerException
from .models import Job, Resource
from .constants import JobStatus, HPCBackend, ScriptType
from .saga_helper import SagaJobWrapper
from .exceptions import JobNotFoundException, FileNotFoundException
import helpers

__author__ = 'Mehdi Sadeghi'


def submit(resource_url, upload_dir, script_type, **kwargs):
    """
    Submit a new job along with its input files. Input files will be moved
    under a new folder with this structure:
        <staging_dir>/<username>/<job_id>/input_files/
    :param resource_url: resource to submit job there
    :param upload_dir: a temp directory which contains uploaded files.
        Any file in that directory starting with `input_' and `script_` would
        be considered as input and script file respectively.
    :param script_type: a value from ScriptType enum to represend script type.
        could be 0 for shell and 1 for python scripts.
    :param kwargs::
        :param name: a user defined name for the job
        :param hpc_backend: type of scheduler on the remote host. Currently
            normal(shell) and sge are supported.
        :param total_cpu_count:
        :param spmd_variation:
        :param walltime_limit:
        :param adaptor: the backend to be used, should be 'shell' or 'sge'
        :param description: about the job
    :return: job id
    """
    # Basic checks
    if not resource_url:
        raise JobManagerException("Resource is not defined.")

    if not upload_dir:
        raise JobManagerException('At least script files should be uploaded')

    # Create a job and fill it with provided information
    job = Job()
    job.owner_id = current_user.id
    job.script_type = ScriptType(script_type).value

    if 'hpc_backend' in kwargs:
        job.hpc_backend = HPCBackend(kwargs.get('hpc_backend')).value

    job.name = kwargs.get('job_name')
    job.remote_dir = kwargs.get('working_directory')
    job.description = kwargs.get('description')
    job.total_cpu_count = kwargs.get('total_cpu_count')
    job.walltime_limit = kwargs.get('walltime_limit')
    job.spmd_variation = kwargs.get('spmd_variation')
    job.queue = kwargs.get('queue')
    job.project = kwargs.get('project')
    job.total_physical_memory = kwargs.get('total_physical_memory')

    try:
        # Insert a new record for url if it does not exist already
        resource = Resource.query.filter(Resource.url == resource_url).first()
        if not resource:
            resource = Resource(resource_url)
            db.session.add(resource)
            db.session.flush()
        job.resource_id = resource.id
        db.session.add(job)
        db.session.flush()

        # Moving temp uploaded files into a directory under job's name
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/
        # Set to silent because some ghost files are uploaded with no name and
        #   empty value, don't know why.
        helpers.stage_uploaded_files(job,
                                     upload_dir,
                                     current_app.config,
                                     silent=True)

        # Submit the job using saga
        saga_wrapper = SagaJobWrapper(job)
        saga_wrapper.run()
    except saga.exceptions.AuthenticationFailed, error:
        db.session.rollback()
        raise JobManagerException('Can not login to the remote host, \
            authentication failed. %s' % error)
    except:
        db.session.rollback()
        raise
    # If no error has happened so far, commit the session.
    db.session.commit()
    return job.id


def get_job_status(job_id):
    """
    Get job updated status
    :param job_id:
    :return:
    """
    job = get_job(job_id)

    # Check if user is allowed to see this job

    if job.id not in g.__jobs:
        if job.last_status not in [JobStatus.CANCELED,
                                   JobStatus.DONE,
                                   JobStatus.FAILED]:
            # If there is not wrapper for the job and the job is not either
            # cancelled, done, or failed, then we don't know what has happened
            # to the job.
            return JobStatus.UNKNOWN

    # If we have the wrapper we trust him to update last_status and we sent
    # the object's status.
    return job.last_status


def _check_access(job):
    """
    Check if current user has access to the given job
    """
    if current_user.is_anonymous and current_app.config.get('LOGIN_DISABLED'):
        # The app is running in single user mode
        return

    if job.owner_id != current_user.id:
        # Users are not allowed to see each other's activities
        abort(403)


def get_job(job_id, *args, **kwargs):
    """
    Get a job
    :job_id: id of the job
    """
    job = Job.query.get(job_id)

    if not job:
        raise JobNotFoundException("Job not found.")

    # Check if current user has access to this job
    _check_access(job)

    return job


def list_jobs(page=None, **kwargs):
    """
    List submitted jobs.
    :param page: page number
    :return: job pagination
    """

    if current_user.is_anonymous and current_app.config.get('LOGIN_DISABLED'):
        # Do not filter. Login is disabled.
        query = Job.query.filter().order_by(Job.submit_date.desc())
    else:
        query = \
            Job.query.filter(Job.owner_id == current_user.id).order_by(
                Job.submit_date.desc())

    return query.paginate(page, current_app.config['PER_PAGE'])


def get_file_location(job_id, file_name):
    """
    Returns the folder of the file
    :param job_id:
    :param file_name:
    :return:
    """
    # If there is a request context get the config
    if current_app is not None:
        config = current_app.config
    job = Job.query.get(job_id)
    if job is None:
        raise JobNotFoundException('Job number %s does not exist.' % job_id)
    for f in job.files:
        if f.name == file_name:
            return helpers.get_job_staging_folder(job.id, config)
    raise \
        FileNotFoundException('Job number %s does not have any file called %s'
                              % (job_id, file_name))


def cancel_job(job_id):
    """
    Cancel a job
    :param job_id:
    :return:
    """
    job = get_job(job_id)
    wrapper = SagaJobWrapper(job)
    wrapper.cancel()
