"""
    sqmpy.job.manager
    ~~~~~

    Manager class along with it's helpers.
"""
import datetime

from flask.ext.login import current_user
from saga.exceptions import BadParameter

from sqmpy import app, db
from sqmpy.core import SQMComponent
from sqmpy.job.exceptions import JobManagerException
from sqmpy.job.helpers import JobFileHandler
from sqmpy.job.models import Job, Resource
from sqmpy.job.constants import JOB_MANAGER, JobStatus, ScriptType
from sqmpy.job.saga_helper import SagaJobWrapper

__author__ = 'Mehdi Sadeghi'


class JobManager(SQMComponent):
    """
    This class is responsible to keep state of the executed jobs.
    """
    def __init__(self):
        super(JobManager, self).__init__(JOB_MANAGER)

        # A dictionary to keep active jobs along with their wrapper objects.
        # Wrapper objects contain the job itself along with related saga objects.
        self.__jobs = {}

    def submit_job(self, name, resource_url, script, script_type, input_files=None, description=None, **kwargs):
        """
        Submit a new job along with its input files. Input files will be moved under
            a new folder with this structure: <staging_dir>/<username>/<job_id>/input_files/
        :param name: job name
        :param resource_url: resource to submit job there
        :param script_type: integer type of the script according to ScriptType enum
        :param script: user script
        :param input_files: a list of <filename, file_stream> for each given file.
        :param description: about the job
        :return: job id
        """
        # Basic checks
        if name is None:
            raise JobManagerException("Job name is not defined.")

        if resource_url in (None, ''):
            raise JobManagerException("Resource is not defined.")

        if script in (None, ''):
            raise JobManagerException('Script could not be empty')

        # Store the job
        job = Job()
        job.name = name
        job.submit_date = datetime.datetime.now()
        job.last_status = JobStatus.INIT
        job.owner_id = current_user.id
        job.user_script = script
        # TODO: Hook to proper script handler, see issue #13 on github
        try:
            # Control if the script_type is known by system, otherwise throw error.
            ScriptType(script_type)
        except ValueError:
            # TODO: May be we could try to guess script type before throwing an error?
            raise JobManagerException('Script type {script_type} is not known'.format(script_type=script_type))
        job.script_type = script_type

        # Insert a new record for url if it does not exist already
        #db.session.begin()
        try:
            resource = Resource.query.filter(Resource.url == resource_url).first()
            if not resource:
                resource = Resource(resource_url, resource_url)
                db.session.add(resource)
                db.session.flush()
            job.resource_id = resource.id
            job.description = description
            db.session.add(job)
            db.session.flush()

            # Save staging data before running the job
            # Input files will be moved under a new folder with this structure:
            #   <staging_dir>/<username>/<job_id>/
            # This will also save script file in the mentioned job folder as `job-[JOB_ID]_script'
            JobFileHandler.save_input_files(job, input_files, script)

            #TODO: I should find a way to either save state or not to save state when error happen.
            # Create saga wrapper
            saga_wrapper = SagaJobWrapper(job)
            # Keep the created job
            self.__jobs[job.id] = saga_wrapper
            # Run the saga job
            saga_wrapper.run()
        except:
            db.session.rollback()
            raise
        db.session.commit()
        return job.id

    def get_job(self, job_id, *args, **kwargs):
        """
        Get a job
        :job_id: id of the job
        """
        job = Job.query.get(job_id)
        if not job:
            raise JobManagerException("Job not found.")
        return Job.query.get(job_id)

    def list_jobs(self, page=None, **kwargs):
        """
        List submitted jobs.
        :param page: page number
        :return: job pagination
        """
        query = Job.query.filter(Job.owner_id == current_user.id).order_by(Job.submit_date.desc())

        return query.paginate(page, app.config['PER_PAGE'])

    def get_file_location(self, job_id, file_name):
        """
        Returns the folder of the file
        :param job_id:
        :param file_name:
        :return:
        """
        return JobFileHandler.get_file_location(job_id, file_name)