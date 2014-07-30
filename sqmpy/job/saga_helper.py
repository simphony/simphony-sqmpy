"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import os
import hashlib
import time
import datetime
import threading

import saga

from sqmpy import app, db
from sqmpy.job.constants import FileRelation, ScriptType
from sqmpy.job.helpers import JobFileHandler, send_state_change_email
from sqmpy.job.models import Resource, StagingFile, JobStateHistory, Job
from sqmpy.security import services as security_services

__author__ = 'Mehdi Sadeghi'


class SagaJobWrapper(object):
    """
    To wrap, initialize and run a saga job.
    """
    def __init__(self, job):
        """
        Init
        :param job: an instance of job model class
        :return:
        """
        self._job_id = job.id
        self._job = job
        self._security_context = None
        self._session = None
        self._job_service = None
        self._job_description = None
        self._saga_job = None
        # Keep the instance of job monitoring thread
        self._monitor_thread = None
        self._logger = app.logger
        self._script_staging_file = None
        #Init everything
        self._initialize()

        # Creating the job service object which represents a machine
        # which we connect to it using ssh (either local or remote)
        self._job_service = \
            saga.job.Service(self._get_remote_job_endpoint(),
                             session=self._session)

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

    def _get_remote_job_endpoint(self):
        """
        Get ssh URI of remote host
        :return:
        """
        backend = 'fork'
        remote_host = 'localhost'
        if self._job.resource_id > 0:
            backend = 'ssh'
            remote_host = self._job.resource.url
        return '{backend}://{remote_host}'.format(backend=backend,
                                                  remote_host=remote_host)

    def _get_remote_job_dir(self):
        """
        Returns the remote job working directory. Creates the parent
        folders if they don't exist.
        :return:
        """
        # Job directory would resist inside sqmpy folder. sqmpy folder
        # Job directory name would be job id. The sqmpy folder will be
        # created in user home folder.
        # TODO: Let user give a working directory for the job or a resource
        # FIXME: Use proper ssh name to find home folder. Currently it is current user_name
        owner = security_services.get_user(self._job.owner_id)
        remote_host = 'localhost'
        if self._job.resource_id > 0:
            remote_host = self._job.resource.url
        remote_address = \
            'sftp://{remote_host}/home/{user_name}/sqmpy/{job_id}'.format(remote_host=remote_host,
                                                                          user_name=owner.name,
                                                                          job_id=self._job.id)
        return \
            saga.filesystem.Directory(remote_address,
                                      saga.filesystem.CREATE_PARENTS,
                                      session=self._session)

    def _create_job_description(self, remote_job_dir):
        """
        Creates saga job description
        :param remote_job_dir: saga remote job directory instance
        :return:
        """
        script_file = \
            StagingFile.query.filter(StagingFile.parent_id == self._job.id,
                                     StagingFile.relation == FileRelation.script.value).first()

        jd = saga.job.Description()
        # TODO: Add queue name, cpu count, project and other params
        jd.working_directory = remote_job_dir.get_url().path

        # TODO: Use script handler instead, see issue #13 on github
        if self._job.script_type == ScriptType.python.value:
            jd.executable = '/usr/bin/python'
        if self._job.script_type == ScriptType.shell.value:
            jd.executable = '/bin/sh'

        # TODO: Add proper arguments for each input file
        jd.arguments = [script_file.name]
        jd.output = '{script_name}.out.txt'.format(script_name=script_file.name)
        jd.error = '{script_name}.err.txt'.format(script_name=script_file.name)
        return jd

    def _upload_job_files(self, remote_job_dir_url):
        """
        Upload job files to remote resource
        :param remote_job_dir_url: saga.url.Url of remote job directory
        :return
        """
        # Copy script and input files to remote host
        uploading_files = \
            StagingFile.query.filter(StagingFile.parent_id == self._job.id,
                                     StagingFile.relation.in_([FileRelation.input.value,
                                                               FileRelation.script.value])).all()
        for file_to_upload in uploading_files:
            file_wrapper = \
                saga.filesystem.File('file://localhost/{file_path}'
                                     .format(file_path=file_to_upload.get_path()))
            file_wrapper.copy(remote_job_dir_url)

    def move_files_back(self):
        """
        Copies output and error files along with any other output files back to server.
        :return:
        """
        # Check if object is bound to session
        # TODO: temporary, maybe i should make all this static to avoid problems
        self._job = Job.query.get(self._job.id)

        # Get or create job directory
        local_job_dir = JobFileHandler.get_job_file_directory(self._job.id)
        local_job_dir_sftp = JobFileHandler.get_job_file_directory(self._job.id, make_sftp_url=True)

        # Get staging file names for this job which are already uploaded
        # we don't need to download them since we have them already
        uploaded_files = \
            StagingFile.query.with_entities(StagingFile.name).filter(StagingFile.parent_id == Job.id,
                                                                     Job.id == self._job.id).all()
        # Convert tuple result to list
        uploaded_files = [file_name for file_name, in uploaded_files]
        #TODO: Check for extra created files and move them back if needed
        remote_dir = self._get_remote_job_dir()
        files = remote_dir.list()
        staging_files = []
        for file_url in files:
            if file_url.path == self._job_description.output:
                staging_files.append((file_url, FileRelation.output.value))
            elif file_url.path == self._job_description.error:
                staging_files.append((file_url, FileRelation.error.value))
            elif file_url.path not in uploaded_files:
                staging_files.append((file_url, FileRelation.output.value))

        for file_url, relation in staging_files:
            # Copy physical file to local directory
            remote_dir.copy(file_url, local_job_dir_sftp)
            # Insert appropriate record into db
            absolute_name = os.path.join(local_job_dir, file_url.path)
            sf = StagingFile()
            sf.name = file_url.path
            sf.relation = relation
            # TODO use safe file name here
            sf.original_name = file_url.path
            sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
            sf.location = local_job_dir
            sf.parent_id = self._job.id
            db.session.add(sf)
        db.session.commit()

    def run(self):
        """
        Run the job on remote resource
        :return:
        """
        # Get resource address
        resource = None
        if self._job.resource_id and self._job.resource_id > 0:
            resource = Resource.query.get(self._job.resource_id)

        # Set remote job working directory
        remote_job_dir = self._get_remote_job_dir()

        # Upload files and get the script file instance back
        self._upload_job_files(remote_job_dir.get_url())

        # Create job description
        self._job_description = self._create_job_description(remote_job_dir)

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
        self._monitor_thread = JobStateChangeMonitor(self._job.id, self._saga_job, self)
        # Begin monitoring
        self._monitor_thread.start()

        # Store remote pid
        self._job.remote_pid = self._saga_job.get_id()
        db.session.commit()

        self._logger.debug("Job ID    : %s" % self._saga_job.id)
        self._logger.debug("Job State : %s" % self._saga_job.state)

        # List all jobs that are known by the adaptor.
        # This should show our job as well.
        self._logger.debug("Listing active jobs: ")
        for job in self._job_service.list():
            self._logger.debug(" * %s" % job)

        # TODO: Where should I close job service properly? I should put it in user session or g?
        #self._job_service.close()


class JobStateChangeMonitor(threading.Thread):
    """
    A timer thread to check job status changes.
    """
    def __init__(self, job_id, saga_job, job_wrapper, db_session=None):
        """
        Initialize the time and job instance
        :param job_id: sqmpy job id
        :param saga_job: a saga job instance
        :param job_wrapper: job wrapper instance
        """
        super(JobStateChangeMonitor, self).__init__()
        self._saga_job = saga_job
        self._job_id = job_id
        self._job_wrapper = job_wrapper
        self._logger = app.logger
        self._db_session = db_session

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
                job = Job.query.get(self._job_id)
                if job.last_status != new_state:
                    send_state_change_email(self._job_id, job.last_status, new_state)
                    job.last_status = new_state
                    #TODO: Which session this really is?
                    db.session.commit()

                # If there are new files, transfer them back, along with output and error files
                # TODO: I should run this in main thread
                with app.app_context():
                    print "Monitoring thread: Staging calling wrapper method"
                    self._job_wrapper.move_files_back()
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
        :param wrapper: job wrapper
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

            pass

        # Update job status
        if self._sqmpy_job.last_status != val:
            # TODO: Make notification an abstract layer which allows adding further means such as twitter
            send_state_change_email(self._sqmpy_job.id, self._sqmpy_job.last_status, val)
            # Insert history record
            history_record = JobStateHistory()
            history_record.change_time = datetime.datetime.now()
            history_record.old_state = self._sqmpy_job.last_status
            history_record.new_state = val
            history_record.job_id = self._sqmpy_job.id
            db.session.add(history_record)

            # Keep the new value
            self._sqmpy_job.last_status = val
            if db.session.object_session(self._sqmpy_job) is None:
                db.session.add(self._sqmpy_job)
            else:
                db.session.object_session(self._sqmpy_job).commit()

            # Remain registered
            db.session.commit()
        return True