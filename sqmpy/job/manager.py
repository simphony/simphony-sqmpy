"""
    sqmpy.job.manager
    ~~~~~

    Manager class along with it's helpers.
"""
import datetime

import saga

from flask_login import current_user

from sqmpy.core import SQMComponent
from sqmpy.database import db_session
from sqmpy.job.exceptions import JobManagerException
from sqmpy.job.models import Job, Resource
from sqmpy.job.constants import JOB_MANAGER, JobStatus

__author__ = 'Mehdi Sadeghi'


class JobManager(SQMComponent):
    """
    This class is responsible to keep state of the executed jobs.
    """

    def __init__(self):
        super(JobManager, self).__init__(JOB_MANAGER)
        self.__jobs = {}
        for job in Job.query.all():
            self.__jobs[job.id] = job

    def submit_job(self, name, resource_id, script, inputfile=None, description=None, **kwargs):
        """
        Submit a new job
        :name: job name
        :resource_id: resource to submit job there
        :script: user script
        :inputfile: input data file if any
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
        job.input_location = ''
        job.output_location = ''
        job.owner_id = current_user.id
        job.user_script = script
        job.description = description
        job.resource_id = resource_id

        db_session.add(job)
        db_session.commit()

        # Add job to self
        self.__jobs[job.id] = job

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
            # Create ssh context
            ctx = saga.Context('ssh')

            #TODO: replace with user defined ssh_id
            #ctx.user_id = ssh_id

            # Create saga session
            session = saga.Session()
            session.add_context(ctx)

            resource = Resource.query.get(job.resource_id)

            # Creatign the job service object which represents a machine
            # which we connect to it using ssh (either local or remote)
            js = saga.job.Service('ssh://{url}'.format(url=resource.url),
                                  session=session)

            # Creating job description
            jd = self._create_job_description(job)

            # Create the job to submit
            saga_job = js.create_job(jd)

            # for logging
            from sqmpy import app

            # Check our job's id and state
            app.logger.debug("Job ID    : %s" % (saga_job.id))
            app.logger.debug("Job State : %s" % (saga_job.state))

            # Run the job eventually
            app.logger.debug("...starting job...")
            saga_job.run()

            app.logger.debug("Job ID    : %s" % (saga_job.id))
            app.logger.debug("Job State : %s" % (saga_job.state))

            # List all jobs that are known by the adaptor.
            # This should show our job as well.
            app.logger.debug("Listing active jobs: ")
            for job in js.list():
                app.logger.debug(" * %s" % job)

            # Wait for the job to complete
            #print "\n...waiting for job...\n"
            #saga_job.wait()

            app.logger.debug("Job State   : %s" % (saga_job.state))
            app.logger.debug("Exitcode    : %s" % (saga_job.exit_code))
            app.logger.debug("Exec. hosts : %s" % (saga_job.execution_hosts))
            app.logger.debug("Create time : %s" % (saga_job.created))
            app.logger.debug("Start time  : %s" % (saga_job.started))
            app.logger.debug("End time    : %s" % (saga_job.finished))

            js.close()

        except saga.SagaException, ex:
            raise JobManagerException(ex.message)

    def _create_job_description(self, job):
        """
        Creates saga job description
        :param job:
        :return:
        """
        jd = saga.job.Description()
        jd.executable = '/bin/sh'
        jd.arguments = ['$FILENAME']
        #jd.queue = ''
        #jd.project = ''
        jd.working_directory = '/W5/sade/'
        jd.output = 'job.out'
        jd.error = 'job.err'

        return jd

    def get_job(self, job_id, *args, **kwargs):
        """
        Get a job
        :job_id: id of the job
        """
        if job_id in self.__jobs:
            return Job.query.get(job_id)
            #return self.__jobs[job_id]
        else:
            raise JobManagerException("Job not found.")

    def list_jobs(self, *args, **kwargs):
        """
        List submitted jobs.
        :return: jobs iterator
        """
        user_jobs = {}
        for job_id, job in self.__jobs.iteritems():
            if job.owner_id == current_user.id:
                user_jobs[job_id] = job
        return user_jobs.iteritems()