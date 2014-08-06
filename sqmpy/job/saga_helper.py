"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import os
import socket
import hashlib
import time
import datetime
import threading

import saga

from flask.ext.login import current_user

from sqmpy import app, db
from sqmpy.job.constants import FileRelation, ScriptType
from sqmpy.job.helpers import JobFileHandler, send_state_change_email
from sqmpy.job.models import Resource, StagingFile, JobStateHistory, Job
from sqmpy.job import services as job_services
from sqmpy.security import services as security_services

__author__ = 'Mehdi Sadeghi'


# To be used with url and user as key and service object as value, I know it is dirty.
_service_cache = {}


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
        endpoint = self._get_resource_endpoint(job.resource.url)
        if (current_user.name, endpoint) in _service_cache:
            self._job_service = _service_cache[(current_user.name, endpoint)]
        else:
            self._job_service = \
                saga.job.Service(endpoint,
                                 session=self._session)
            _service_cache[(current_user, endpoint)] = self._job_service
        print "end of init...."

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

    @staticmethod
    def _is_localhost(host):
        """
        Return true if is localhost
        :param host: url
        :return:
        """
        if host in ('localhost',
                    '127.0.0.1',
                    socket.gethostname(),
                    socket.gethostbyname(socket.gethostname())):
            return True
        return False

    # TODO: move this function into a helper module
    def _get_resource_endpoint(self, host):
        """
        Get ssh URI of remote host
        :param host: host to make url for it
        :return:
        """
        backend = 'ssh'
        if SagaJobWrapper._is_localhost(host):
            backend = 'fork'
        return '{backend}://{remote_host}'.format(backend=backend,
                                                  remote_host=host)

    @staticmethod
    def get_job_endpoint(job_id, session):
        """
        Returns the remote job working directory. Creates the parent
        folders if they don't exist.
        :param job_id: job id
        :param session: saga session to be used
        :return:
        """
        job = job_services.get_job(job_id)
        # Job directory would resist inside sqmpy folder. sqmpy folder
        # Job directory name would be job id. The sqmpy folder will be
        # created in user home folder.
        # TODO: Let user give a working directory for the job or a resource
        # FIXME: Use proper ssh name to find home folder. Currently it is current user_name
        owner = security_services.get_user(job.owner_id)
        adapter = 'sftp'
        if SagaJobWrapper._is_localhost(job.resource.url):
            adapter = 'file'
        remote_address = \
            '{adapter}://{remote_host}/home/{user_name}/sqmpy/{job_id}'.format(adapter=adapter,
                                                                               remote_host=job.resource.url,
                                                                               user_name=owner.name,
                                                                               job_id=job.id)
        return \
            saga.filesystem.Directory(remote_address,
                                      saga.filesystem.CREATE_PARENTS,
                                      session=session)

    @staticmethod
    def _create_job_description(job, remote_job_dir):
        """
        Creates saga job description
        :param job: job instance
        :param remote_job_dir: saga remote job directory instance
        :return:
        """
        script_file = \
            StagingFile.query.filter(StagingFile.parent_id == job.id,
                                     StagingFile.relation == FileRelation.script.value).first()

        jd = saga.job.Description()
        # TODO: Add queue name, cpu count, project and other params
        jd.working_directory = remote_job_dir.get_url().path

        # TODO: Use script handler instead, see issue #13 on github
        if job.script_type == ScriptType.python.value:
            jd.executable = '/usr/bin/python'
        if job.script_type == ScriptType.shell.value:
            jd.executable = '/bin/sh'

        # TODO: Add proper arguments for each input file
        jd.arguments = [script_file.name]
        jd.output = '{script_name}.out.txt'.format(script_name=script_file.name)
        jd.error = '{script_name}.err.txt'.format(script_name=script_file.name)
        return jd

    @staticmethod
    def _upload_job_files(job_id, remote_job_dir_url):
        """
        Upload job files to remote resource
        :param job_id: job id
        :param remote_job_dir_url: saga.url.Url of remote job directory
        :return
        """
        # Copy script and input files to remote host
        uploading_files = \
            StagingFile.query.filter(StagingFile.parent_id == job_id,
                                     StagingFile.relation.in_([FileRelation.input.value,
                                                               FileRelation.script.value])).all()
        for file_to_upload in uploading_files:
            file_wrapper = \
                saga.filesystem.File('file://localhost/{file_path}'
                                     .format(file_path=file_to_upload.get_path()))
            file_wrapper.copy(remote_job_dir_url)

    def get_job(self):
        """
        Returns the inner job
        :return:
        """
        return self._job

    def get_saga_session(self):
        """
        Get saga session and context
        :return:
        """
        return self._session

    #todo: change name to download and the variable to ignore and upload
    @staticmethod
    def move_files_back(job_id, job_description, session, wipe=True):
        """
        Copies output and error files along with any other output files back to server.
        :param job_id: job id
        :param job_description:
        :param session: saga session to remote resource
        :param wipe: if set to True will wipe files from remote machine.
        :return:
        """
        # Get a new object in this session
        job = Job.query.get(job_id)

        # Get or create job directory
        local_job_dir = JobFileHandler.get_job_file_directory(job_id)
        local_job_dir_url = None
        if SagaJobWrapper._is_localhost(job.resource.url):
            local_job_dir_url = local_job_dir
        else:
            local_job_dir_url = JobFileHandler.get_job_file_directory(job_id, make_sftp_url=True)

        # Get staging file names for this job which are already uploaded
        # we don't need to download them since we have them already
        uploaded_files = \
            StagingFile.query.with_entities(StagingFile.name).filter(StagingFile.parent_id == Job.id,
                                                                     Job.id == job_id).all()
        # Convert tuple result to list
        uploaded_files = [file_name for file_name, in uploaded_files]
        #TODO: Check for extra created files and move them back if needed
        remote_dir = SagaJobWrapper.get_job_endpoint(job_id, session)
        files = remote_dir.list()
        staging_files = []
        for file_url in files:
            if file_url.path == job_description.output:
                staging_files.append((file_url, FileRelation.output.value))
            elif file_url.path == job_description.error:
                staging_files.append((file_url, FileRelation.error.value))
            elif file_url.path not in uploaded_files:
                staging_files.append((file_url, FileRelation.output.value))

        for file_url, relation in staging_files:
            # Copy physical file to local directory
            #TODO: Send notification with download links
            if wipe:
                remote_dir.move(file_url, local_job_dir_url)
            else:
                remote_dir.copy(file_url, local_job_dir_url)
            time.sleep(.5)
            # Insert appropriate record into db
            absolute_name = os.path.join(local_job_dir, file_url.path)
            sf = StagingFile()
            sf.name = file_url.path
            sf.relation = relation
            # TODO use safe file name here
            sf.original_name = file_url.path
            sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
            sf.location = local_job_dir
            sf.parent_id = job_id
            db.session.add(sf)
        db.session.commit()

    def run(self):
        """
        Run the job on remote resource
        :return:
        """
        self._logger.debug("...very beginning...")
        # Get resource address
        resource = None
        if self._job.resource_id and self._job.resource_id > 0:
            resource = Resource.query.get(self._job.resource_id)

        # Set remote job working directory
        remote_job_dir = SagaJobWrapper.get_job_endpoint(self._job.id, self._session)

        # Upload files and get the script file instance back
        self._upload_job_files(self._job.id, remote_job_dir.get_url())

        # Create job description
        self._job_description = self._create_job_description(self._job, remote_job_dir)

        # Create saga job
        self._saga_job = self._job_service.create_job(self._job_description)

        # Register call backs
        self._register_callbacks()

        # Check our job's id and state
        self._logger.debug("Job ID    : %s" % self._saga_job.id)
        self._logger.debug("Job State : %s" % self._saga_job.state)

        # To be used for stopping the thread
        stop_event = threading.Event()

        try:
            # Run the job eventually
            self._logger.debug("...starting job...")
            self._saga_job.run()

            # Create the monitoring thread
            self._monitor_thread = JobStateChangeMonitor(self._job.id, self._saga_job, self, stop_event)
            # Begin monitoring
            self._monitor_thread.start()

            # Store remote pid
            self._job.remote_pid = self._saga_job.get_id()
            db.session.flush()
        except:
            # Todo: Find a way to gracefully stop the monitoring thread
            stop_event.set()
            raise

        self._logger.debug("Job ID    : %s" % self._saga_job.id)
        self._logger.debug("Job State : %s" % self._saga_job.state)

        # List all jobs that are known by the adaptor.
        # This should show our job as well.
        self._logger.debug("Listing active jobs: ")
        for job in self._job_service.list():
            self._logger.debug(" * %s" % job)

        # TODO: Where should I close job service properly? I should put it in user session or g?
        #self._job_service.close()

    def get_job_description(self):
        """
        Returns job description object
        """
        return self._job_description


class JobStateChangeMonitor(threading.Thread):
    """
    A timer thread to check job status changes.
    """
    def __init__(self, job_id, saga_job, job_wrapper, stop_event):
        """
        Initialize the time and job instance
        :param job_id: sqmpy job id
        :param saga_job: a saga job instance
        :param job_wrapper: job wrapper instance
        :param stop_event: threading.Event instance for listning to it
        """
        super(JobStateChangeMonitor, self).__init__()
        self._saga_job = saga_job
        self._job_id = job_id
        self._job_wrapper = job_wrapper
        self._stop_event = stop_event
        self._logger = app.logger
        self._remote_dir = SagaJobWrapper.get_job_endpoint(job_id, self._job_wrapper.get_saga_session())
        self._last_file_names = []

    def run(self):
        """
        Start the timer and keep watching until the job state is done, failed or canceled.
        Right now this thread only reads the status and this cause the saga callbacks
        to be triggered.
        """
        while not self._stop_event.is_set():
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
                job = job_services.get_job(self._job_id)
                if job.last_status != new_state:
                    send_state_change_email(self._job_id, job.owner_id, job.last_status, new_state)
                    job.last_status = new_state
                    #TODO: Which session this really is?
                    db.session.flush()

                # If there are new files, transfer them back, along with output and error files
                SagaJobWrapper.move_files_back(self._job_id,
                                               self._job_wrapper.get_job_description(),
                                               self._job_wrapper.get_saga_session())

                # TODO: I should run this in main thread
                #with app.app_context():
                #    print "Monitoring thread: Staging calling wrapper method"
                #    SagaJobWrapper.move_files_back(self._job_wrapper.get_job_description())
                return
            else:
                # Check if there are new files to process
                #remote_dir = SagaJobWrapper._get_job_endpoint(job_id, session)
                file_urls = self._remote_dir.list()
                update_flag = False
                for file_url in file_urls:
                    if file_url.path not in self._last_file_names:
                        self._last_file_names.append(file_url.path)
                        update_flag = True
                if update_flag:
                    SagaJobWrapper.move_files_back(self._job_id,
                                                   self._job_wrapper.get_job_description(),
                                                   self._job_wrapper.get_saga_session())

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
        #if val in (saga.DONE, saga.FAILED, saga.EXCEPTION, saga):
        #    pass

        with db.session.begin_nested:

            # Avoid threading errors
            if self._sqmpy_job not in db.session:
                db.session.merge(self._sqmpy_job)

            # Update job status
            if self._sqmpy_job.last_status != val:
                # TODO: Make notification an abstract layer which allows adding further means such as twitter
                send_state_change_email(self._sqmpy_job.id, self._sqmpy_job.owner_id, self._sqmpy_job.last_status, val)
                # Insert history record
                history_record = JobStateHistory()
                history_record.change_time = datetime.datetime.now()
                history_record.old_state = self._sqmpy_job.last_status
                history_record.new_state = val
                history_record.job_id = self._sqmpy_job.id
                db.session.add(history_record)

                # Keep the new value
                self._sqmpy_job.last_status = val

                db.session.flush()

        # Remain registered
        return True
