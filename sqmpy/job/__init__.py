"""
    sqmpy.job
    ~~~~~~~~~~~~~~~~

    Provides job submission and monitoring.
"""
import datetime

import saga

from flask import Blueprint
from flask_login import current_user

from sqmpy.core import SQMComponent, core_services
from sqmpy.database import db_session
from sqmpy.job.models import Job, Resource
from sqmpy.job.constants import JOB_MANAGER, JobStatus

__author__ = 'Mehdi Sadeghi'


class JobManagerException(Exception):
    """
    Represents job manager exceptions
    """


class JobManager(SQMComponent):
    """ 
    This class is responsible to keep state of the executed jobs.
    """

    def __init__(self):
        super(JobManager, self).__init__(JOB_MANAGER)
        self.__jobs = {}
        for job in Job.query.all():
            self.__jobs[job.name] = job

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

        if name in self.__jobs:
            raise JobManagerException("Job with name {name} already registered")

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

        # Add job to self
        self.__jobs[job.name] = job

        # Submit the job to the queue
        self._run(job)

        db_session.add(job)
        db_session.commit()

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

            # Check our job's id and state
            print "Job ID    : %s" % (saga_job.id)
            print "Job State : %s" % (saga_job.state)

            # Run the job eventually
            print "\n...starting job...\n"
            saga_job.run()

            print "Job ID    : %s" % (saga_job.id)
            print "Job State : %s" % (saga_job.state)

            # List all jobs that are known by the adaptor.
            # This should show our job as well.
            print "\nListing active jobs: "
            for job in js.list():
                print " * %s" % job

            # Wait for the job to complete
            print "\n...waiting for job...\n"
            saga_job.wait()

            print "Job State   : %s" % (saga_job.state)
            print "Exitcode    : %s" % (saga_job.exit_code)
            print "Exec. hosts : %s" % (saga_job.execution_hosts)
            print "Create time : %s" % (saga_job.created)
            print "Start time  : %s" % (saga_job.started)
            print "End time    : %s" % (saga_job.finished)

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

    def get_job(self, job_name, *args, **kwargs):
        """
        Get a job
        :job_name: name of the job
        """
        if job_name in self.__jobs:
            return self.__jobs[job_name]

    def list_jobs(self, *args, **kwargs):
        """
        List submitted jobs.
        :return: jobs iterator
        """
        user_jobs = {}
        for job_name, job in self.__jobs.iteritems():
            if job.owner_id == current_user.id:
                user_jobs[job_name] = job
        return user_jobs.iteritems()


job_blueprint = Blueprint('sqmpy.job', __name__)

@job_blueprint.context_processor
def job_cnx_processor():
    return dict(active_page='job')

#Register the component in core
#@TODO: This should be dynamic later
core_services.register(JobManager())