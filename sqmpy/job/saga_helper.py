"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import time
import smtplib
import datetime
import threading
from email.mime.text import MIMEText

import saga

from sqmpy.database import db_session
from sqmpy.job.constants import FileRelation
from sqmpy.job.exceptions import JobManagerException
from sqmpy.job.models import Resource, StagingFile, JobStateHistory
#from sqmpy.security import services as security_services

__author__ = 'Mehdi Sadeghi'


def send_state_change_email(job_id, old_state, new_state):
    """
    A simple helper class to send smtp email for job state change
    :param job_id: Job id in database
    :param old_state:
    :param new_state:
    :return:
    """
    from sqmpy import app
    from sqmpy.security.models import User
    from sqmpy.job.models import Job
    from sqmpy.database import db_session
    owner_email = db_session.query(User.email).filter(User.id == Job.owner_id, Job.id == job_id).one()[0]

    #job_owner = security_services.get_user(self._sqmpy_job.owner_id)
    try:
        smtp_server = smtplib.SMTP(app.config.get('MAIL_SERVER'))
        message = \
            'Status changed from {old} to {new}'.format(old=old_state,
                                                        new=new_state)
        message = MIMEText(message)
        message['Subject'] = 'Change in job number [{job_id}]'.format(job_id=job_id)
        message['From'] = 'monitor@sqmpy'
        message['To'] = owner_email
        smtp_server.sendmail('sade@iwm.fraunhofer.de',
                             [owner_email],
                             message.as_string())
        smtp_server.quit()
    except smtplib.SMTPException, ex:
        from sqmpy import app
        app.logger.debug("Callback: Failed to send mail: %s" % ex)


class JobStateChangeMonitor(threading.Thread):
    """
    A timer thread to check job status changes.
    """
    def __init__(self, job_id, saga_job):
        """
        Initialize the time and job instance
        :param job_id: sqmpy job id
        :param saga_job: a saga job instance
        """
        super(JobStateChangeMonitor, self).__init__()
        self._saga_job = saga_job
        self._job_id = job_id
        from sqmpy import app
        self._logger = app.logger

    def run(self):
        """
        Start the timer and keep watching until the job state is done, failed or canceled.
        Right now this thread only reads the status and this cause the saga callbacks
        to be triggered.
        """
        while True:
            new_state = self._saga_job.state
            self._logger.debug("Monitoring thread: Job ID    : %s" % self._saga_job.id)
            print "Monitoring thread: Job ID    : %s" % self._saga_job.id
            self._logger.debug("Monitoring thread: Job State : %s" % new_state)
            print "Monitoring thread: Job State : %s" % new_state
            if new_state in (saga.DONE,
                             saga.FAILED,
                             saga.CANCELED):
                # Fixme Here I have to double check if the value is stored correctly.
                # There is a problem that if the job is done and we query job's state
                # the registered callbacks would not be called. So I wait here for a
                # few seconds and afterwards I check the last status and update it if
                # necessary.
                time.sleep(3)
                from sqmpy.database import db_session
                from sqmpy.job.models import Job
                job = Job.query.get(self._job_id)
                if job.last_status != new_state:
                    send_state_change_email(self._job_id, job.last_status, new_state)
                    job.last_status = new_state
                    db_session.commit()
                return

            # Check every 3 seconds
            # TODO Read monitor interval period from application config
            time.sleep(5)


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
        app.logger.debug("Callback: Job ID   : %s" % self._sqmpy_job.id)
        app.logger.debug("Callback: Job Name   : %s" % self._sqmpy_job.name)
        app.logger.debug("Callback: Job Current State   : %s" % saga_job.state)
        app.logger.debug("Callback: Exitcode    : %s" % saga_job.exit_code)
        app.logger.debug("Callback: Exec. hosts : %s" % saga_job.execution_hosts)
        app.logger.debug("Callback: Create time : %s" % saga_job.created)
        app.logger.debug("Callback: Start time  : %s" % saga_job.started)
        app.logger.debug("Callback: End time    : %s" % saga_job.finished)

        # If the job is complete transfer files if any
        if val in (saga.DONE, saga.FAILED, saga.EXCEPTION, saga):
            #TODO: Inform the user about the event, add notify manager
            pass

        # Update job status
        if self._sqmpy_job.last_status != val:
            send_state_change_email(self._sqmpy_job.id, self._sqmpy_job.last_status, val)
            # Insert history record
            history_record = JobStateHistory()
            history_record.change_time = datetime.datetime.now()
            history_record.old_state = self._sqmpy_job.last_status
            history_record.new_state = val
            history_record.job_id = self._sqmpy_job.id
            db_session.add(history_record)

            # Keep the new value
            self._sqmpy_job.last_status = val
            if db_session.object_session(self._sqmpy_job) is None:
                db_session.add(self._sqmpy_job)
            else:
                db_session.object_session(self._sqmpy_job).commit()

            # Remain registered
            db_session.commit()
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
        # SAGA remote directory object representing remote job folder
        self._remote_job_dir = None
        self._saga_job = None
        # Keep the instance of job monitoring thread
        self._monitor_thread = None
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
        # Email notification callback
        #self._saga_job.add_callback(saga.STATE, JobStateChangeNotifyCallback(self._job))

    def _get_remote_job_endpoint(self):
        """
        Get ssh URI of remote host
        :return:
        """
        return 'ssh://{remote_host}'.format(remote_host=self._job.resource.url)

    def _get_remote_dir(self):
        """
        Get remote working directory
        :return:
        """
        return '/W5/sade'

    def _get_remote_file_endpoint(self):
        """
        Get remote file endpoint
        :return:
        """
        # Saga only supports sftp for now, see: http://saga-project.github.io/saga-python/doc/tutorial/part5.html
        return 'sftp://{remote_host}/{remote_dir}'.format(remote_host=self._job.resource.url,
                                                          remote_dir=self._get_remote_dir())

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
            saga.job.Service(self._get_remote_job_endpoint(),
                             session=self._session)

        # Set remote job working directory
        self._remote_job_dir = \
            saga.filesystem.Directory(self._get_remote_file_endpoint(),
                                      saga.filesystem.CREATE,
                                      session=self._session)

        # Copy script and input files to remote host
        script_file = \
            StagingFile.query.filter(StagingFile.parent_id == self._job.id,
                                     StagingFile.relation == FileRelation.SCRIPT.value).first()
        if script_file is None:
            raise JobManagerException('Script could not be empty')
        script_wrapper = \
            saga.filesystem.File('file://localhost/{file_path}'
                                 .format(file_path=script_file.get_path()))
        script_wrapper.copy(self._remote_job_dir.get_url())
        #TODO: Copy all input files to remote directory to pass them to the script

        # Create job description
        self._job_description = self._create_job_description(script_file)

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

        # Create the monitoring thread
        self._monitor_thread = JobStateChangeMonitor(self._job.id, self._saga_job)
        # Begin monitoring
        self._monitor_thread.start()

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

        #self._job_service.close()

    def _create_job_description(self, script_file):
        """
        Creates saga job description
        :param script_file: the script StagingFile object
        :return:
        """
        assert isinstance(script_file, StagingFile)

        jd = saga.job.Description()
        #TODO: Add queue name, cpu count, project and other params
        jd.working_directory = self._remote_job_dir.get_url().path
        jd.executable = '/bin/sh'
        #TODO: Add proper arguments for each input file
        jd.arguments = [script_file.name]
        jd.output = '{script_name}.out'.format(script_name=script_file.name)
        jd.error = '{script_name}.err'.format(script_name=script_file.name)
        return jd