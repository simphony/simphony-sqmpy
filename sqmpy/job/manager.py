"""
    sqmpy.job.manager
    ~~~~~

    Manager class along with it's helpers.
"""
import os
import hashlib
import datetime

import saga

from flask.ext.login import current_user

from sqmpy.core import SQMComponent
from sqmpy.database import db_session
from sqmpy.job.exceptions import JobManagerException, JobNotFoundException, FileNotFoundException
from sqmpy.job.models import Job, Resource, StagingFile
from sqmpy.job.constants import JOB_MANAGER, JobStatus, FileRelation
from sqmpy.job.saga_helper import JobStateChangeCallback, SagaJobWrapper

__author__ = 'Mehdi Sadeghi'


class JobManager(SQMComponent):
    """
    This class is responsible to keep state of the executed jobs.
    """
    # Under use staging directory one folder with this name will be created to
    # store job's input files
    INPUT_FILES_DIR = 'input_files'

    def __init__(self):
        super(JobManager, self).__init__(JOB_MANAGER)
        self.__jobs = {}

    def submit_job(self, name, resource_id, script, input_files=None, description=None, **kwargs):
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
        job.resource_id = resource_id
        job.description = description

        db_session.add(job)
        db_session.commit()

        # Save staging data before running the job
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/input_files/
        JobInputFileHandler.save_input_files(job, input_files)

        # Add job to self
        self.__jobs[job.id] = (job, None)

        # Submit the job to the queue
        self._run(job)

        return job.id

    def _run(self, job):
        """
        Run the given job on it's resource
        :param job: job instance
        :return: None
        """
        assert isinstance(job, Job)

        # Use SAGA to submit the job
        try:
            # Create saga wrapper
            saga_wrapper = SagaJobWrapper(job)

            # Assign the wrapper to the currently runnign job
            self.__jobs[job.id] = (job, saga_wrapper)

            # Run the saga job
            saga_wrapper.run()

        except saga.SagaException, ex:
            raise JobManagerException(ex.message)

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
        for job in Job.query.all():
            if job.owner_id == current_user.id:
                user_jobs[job.id] = job
        return user_jobs.iteritems()


class JobInputFileHandler(object):
    """
    To save input files of the job in appropriate folders and insert records for them.
    """
    @staticmethod
    def save_input_files(job, input_files):
        """
        Saves input files of the given job in appropriate folders
        :param job:
        :param input_files: list of (file_name, file_buffer)
        :return:
        """
        # Save staging data before running the job
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/input_files/
        if input_files is not None:
            job_dir = JobInputFileHandler._get_job_file_directory(job.id)
            for file_name, file_buffer in input_files:
                if file_name is not None and file_buffer is not None:
                    #file_uuid = str(uuid.uuid4())
                    #absolute_name = os.path.join(job_dir, file_uuid)
                    absolute_name = os.path.join(job_dir, file_name)
                    f = open(absolute_name, 'w')
                    # Copy file buffer into destination
                    from shutil import copyfileobj
                    copyfileobj(file_buffer, f, 16384)
                    f.close()
                    sf = StagingFile()
                    sf.name = file_name
                    sf.relation = FileRelation.INPUT
                    sf.original_name = file_name
                    sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
                    sf.location = job_dir
                    sf.parent_id = job.id
                    db_session.add(sf)
                else:
                    raise JobManagerException("Invalid file name or path")
            db_session.commit()

    @staticmethod
    def _get_job_file_directory(job_id):
        """
        Returns the directory which contains job files
        :param job_id:
        :return:
        """
        from sqmpy import app
        user_dir = os.path.join(app.config['STAGING_FOLDER'], current_user.name)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        job_dir = os.path.join(user_dir, str(job_id))
        if not os.path.exists(job_dir):
            os.makedirs(job_dir)
        return job_dir

    @staticmethod
    def get_file_location(job_id, file_name):
        """
        Returns the folder of the file
        :param job_id:
        :param file_name:
        :return:
        """
        job = Job.query.get(job_id)
        if job is None:
            raise JobNotFoundException('Job number %s does not exist.' % job_id)
        for f in job.files:
            if f.name == file_name:
                return JobInputFileHandler._get_job_file_directory(job.id)
        raise FileNotFoundException('Job number %s does not have any file called %s' % (job_id, file_name))