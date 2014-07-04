"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import saga

from sqmpy.database import db_session
from sqmpy.job.models import Job, Resource, StagingFile

__author__ = 'Mehdi Sadeghi'


class NotifyCallback(saga.Callback):
    """
    A call back to notify user about job state changes
    """
    def __init__(self, job):
        """
        Initializing callback with an instance of sqmpy job
        :param job: sqmpy job
        :return:
        """
        self._sqmpy_job = job

    def cb(self, obj, key, val):
        """
        Callback itself.
        :param obj: the watched object instance
        :param key:the watched attribute, e.g. state or state_detail
        :param val:the new value of the watched attribute
        :return:
        """
        # Notify user

        # Remain registered
        return True


class JobStateChangeCallback(saga.Callback):
    """
    Handle job state changes
    """
    def __init__(self, job):
        """
        Initializing callback with an instance of sqmpy job
        :param job: sqmpy job
        :return:
        """
        self._sqmpy_job = job

    def cb(self, obj, key, val):
        """
        Callback itself.
        :param obj: the watched object instance
        :param key:the watched attribute, e.g. state or state_detail
        :param val:the new value of the watched attribute
        :return:
        """
        from sqmpy import app
        saga_job = obj
        app.logger.debug("### Job State Change Report")
        app.logger.debug("Job ID   : %s" % self._sqmpy_job.id)
        app.logger.debug("Job Name   : %s" % self._sqmpy_job.name)
        app.logger.debug("Job Current State   : %s" % saga_job.state)
        app.logger.debug("Exitcode    : %s" % saga_job.exit_code)
        app.logger.debug("Exec. hosts : %s" % saga_job.execution_hosts)
        app.logger.debug("Create time : %s" % saga_job.created)
        app.logger.debug("Start time  : %s" % saga_job.started)
        app.logger.debug("End time    : %s" % saga_job.finished)

        # If the job is complete transfer files if any
        if val == saga.DONE:
            pass

        # Remain registered
        return True


class SagaJobWrapper(object):
    """
    To wrap, initialize and run a saga job.
    """
    def __init__(self, sqmpy_job):
        """
        Init
        :param sqmpy_job: an instance of sqmpy job
        :return:
        """
        self._job = sqmpy_job
        self._security_context = None
        self._session = None
        self._job_service = None
        self._job_description = None
        self._saga_job = None
        from sqmpy import app
        self._logger = app.logger

        #Init everything
        self._initialize()

    def _initialize(self):
        """
        Do job initialization
        :return:
        """
        # Create security context
        self._security_context = saga.Context('ssh')

        # Create session
        self._session = saga.Session()

        # Add security context to session
        self._session.add_context(self._security_context)

    def _register_callbacks(self):
        """
        Register callback functions for the saga job
        :return:
        """
        #TODO Add a hook here to register any callbacks
        # This callback should store output files locally and store new status in db
        self._saga_job.add_callback(saga.STATE, JobStateChangeCallback(self._job))

    def run(self):
        """
        Run the job on remote resource
        :return:
        """
        # Get resource address
        resource = Resource.query.get(self._job.resource_id)

        # Creating the job service object which represents a machine
        # which we connect to it using ssh (either local or remote)
        self._job_service = \
            saga.job.Service('ssh://{url}'.format(url=resource.url),
                             session=self._session)

        # Create job description
        self._job_description = self._create_job_description()

        # Create saga job
        self._saga_job = self._job_service.create_job(self._job_description)

        # Register call backs
        self._register_callbacks()

        # Check our job's id and state
        self._logger.debug("Job ID    : %s" % self._saga_job.id)
        self._logger.debug("Job State : %s" % self._saga_job.state)

        # Run the job eventually
        self._logger.debug("...starting job...")
        self._saga_job.run()

        # Store remote pid
        self._job.remote_pid = self._saga_job.get_id()
        db_session.commit()

        self._logger.debug("Job ID    : %s" % self._saga_job.id)
        self._logger.debug("Job State : %s" % self._saga_job.state)

        # List all jobs that are known by the adaptor.
        # This should show our job as well.
        self._logger.debug("Listing active jobs: ")
        for job in self._job_service.list():
            self._logger.debug(" * %s" % job)

        self._job_service.close()

    def _create_job_description(self):
        """
        Creates saga job description
        :param job:
        :return:
        """
        self._job.resource_id
        jd = saga.job.Description()
        jd.executable = '/bin/sh'
        jd.arguments = ['$FILENAME']
        #jd.queue = ''
        #jd.project = ''
        jd.working_directory = '/W5/sade/'
        jd.output = 'job.out'
        jd.error = 'job.err'

        return jd