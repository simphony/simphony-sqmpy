"""
    sqmpy.job.manager
    ~~~~~

    Manager class along with it's helpers.
"""
import datetime

from flask.ext.login import current_user

from sqmpy import db
from sqmpy.core import SQMComponent
from sqmpy.job.exceptions import JobManagerException
from sqmpy.job.helpers import JobInputFileHandler
from sqmpy.job.models import Job
from sqmpy.job.constants import JOB_MANAGER, JobStatus
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

    def submit_job(self, name, resource_id, script, script_type, input_files=None, description=None, **kwargs):
        """
        Submit a new job along with its input files. Input files will be moved under
            a new folder with this structure: <staging_dir>/<username>/<job_id>/input_files/
        :param name: job name
        :param resource_id: resource to submit job there
        :param script_type: integer type of the script according to ScriptType enum
        :param script: user script
        :param input_files: a list of <filename, file_stream> for each given file.
        :param description: about the job
        :return: job id
        """
        # Basic checks
        if name is None:
            raise JobManagerException("Job name is not defined.")

        if resource_id is None:
            raise JobManagerException("Resource is not defined.")

        if script in (None, ''):
            raise JobManagerException("Script is not valid.")

        # Store the job
        job = Job()
        job.name = name
        job.submit_date = datetime.datetime.now()
        job.last_status = JobStatus.INIT
        job.owner_id = current_user.id
        job.user_script = script
        job.script_type = script_type
        job.resource_id = resource_id
        job.description = description

        db.session.add(job)
        db.session.commit()

        # Save staging data before running the job
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/
        # This will also save script file in the mentioned job folder as `job-[JOB_ID]_script'
        JobInputFileHandler.save_input_files(job, input_files, script)

        # Create saga wrapper
        saga_wrapper = SagaJobWrapper(job)

        # Add job to self
        self.__jobs[job.id] = saga_wrapper

        # Run the saga job
        saga_wrapper.run()

        # Submit the job to the queue
#        self._run(job)

        return job.id

    # def _run(self, job):
    #     """
    #     Run the given job on it's resource
    #     :param job: job instance
    #     :return: None
    #     """
    #     assert isinstance(job, Job)
    #
    #     # Use SAGA to submit the job
    #     try:
    #         # Get saga wrapper
    #         saga_wrapper = self.__jobs[job.id]
    #
    #         # Run the saga job
    #         saga_wrapper.run()
    #
    #     except saga.SagaException, ex:
    #         raise JobManagerException(ex.message)

    def get_job(self, job_id, *args, **kwargs):
        """
        Get a job
        :job_id: id of the job
        """
        job = Job.query.get(job_id)
        if not job:
            raise JobManagerException("Job not found.")
        return Job.query.get(job_id)

    def list_jobs(self, *args, **kwargs):
        """
        List submitted jobs.
        :return: jobs iterator
        """
        user_jobs = {}
        for job in Job.query.filter(Job.owner_id == current_user.id):
            user_jobs[job.id] = job

        return user_jobs

    def get_file_location(self, job_id, file_name):
        """
        Returns the folder of the file
        :param job_id:
        :param file_name:
        :return:
        """
        return JobInputFileHandler.get_file_location(job_id, file_name)