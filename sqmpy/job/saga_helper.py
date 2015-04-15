"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import datetime

import saga
from flask import current_app, copy_current_request_context

from ..models import db
from .constants import FileRelation, ScriptType, Adaptor
from .exceptions import JobManagerException
from .models import Resource, StagingFile, JobStateHistory, Job
import helpers
from sqmpy.job.callback import JobStateChangeCallback

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
        self._job_description = None
        self._saga_job = None
        self._logger = current_app.logger
        self._script_staging_file = None

        # Create ssh security context
        self._security_context = saga.Context('ssh')
        self._session = saga.Session()
        self._session.add_context(self._security_context)

        # TODO: Remove this and replace redis or database
        # Creating the job service object which represents a machine
        # which we connect to it using ssh (either local or remote)
        endpoint = helpers.get_resource_endpoint(job.resource.url, job.submit_adaptor)
        self._job_service = \
            saga.job.Service(endpoint,
                             session=self._session)

    def _register_callbacks(self):
        """
        Register callback functions for the saga job
        :return:
        """
        # This callback will locally store output files and new states in db
        self._saga_job.add_callback(saga.STATE, JobStateChangeCallback(self._job, self))


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
        # TODO: Add queue name, project and other params
        jd.working_directory = remote_job_dir.get_url().path
        jd.total_cpu_count = job.total_cpu_count
        jd.wall_time_limit = job.walltime_limit
        jd.spmd_variation = job.spmd_variation
        jd.queue = job.queue or None
        jd.total_physical_memory = job.total_physical_memory or None
        jd.project = job.project or None

        # TODO: Add proper arguments for each input file
        jd.arguments = [script_file.name]

        # TODO: Use script handler instead, see issue #13 on github
        if job.submit_adaptor == Adaptor.shell.value:
            if job.script_type == ScriptType.python.value:
                jd.executable = '/usr/bin/python'
            if job.script_type == ScriptType.shell.value:
                jd.executable = '/bin/sh'
        else:
            jd.executable = '/bin/sh'
            script_abs_path = '{dir}/{file}'.format(dir=remote_job_dir.get_url().path,
                                                    file=script_file.name)
            jd.arguments = [script_abs_path]

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
        remote_job_dir = helpers.get_job_endpoint(self._job.id, self._session)
        if remote_job_dir.list():
            raise JobManagerException('Remote directory is not empty')

        # Upload files and get the script file instance back
        self._upload_job_files(self._job.id, remote_job_dir.get_url())

        # Create job description
        self._job_description = self._create_job_description(self._job, remote_job_dir)

        # Create saga job
        self._saga_job = self._job_service.create_job(self._job_description)

        # Register call backs
        #self._register_callbacks()

        # TODO: My monitoring approach is wrong and should be changed.
        # Prepare our gevent greenlet
        import gevent
        @copy_current_request_context
        def monitor_state():
            while True:
                gevent.sleep(3)
                try:
                    val = self._saga_job.state
                    if val != self._job.last_status:
                        # Shout out load
                        try:
                            helpers.send_state_change_email(self._job.id,
                                                            self._job.owner_id,
                                                            self._job.last_status,
                                                            val)
                        except Exception, ex:
                            current_app.logger.debug("Callback: Failed to send mail: %s" % ex)
                        # Insert history record
                        history_record = JobStateHistory()
                        history_record.change_time = datetime.datetime.now()
                        history_record.old_state = self._job.last_status
                        history_record.new_state = val
                        history_record.job_id = self._job.id
                        db.session.add(history_record)
                        db.session.flush()
                        # If there are new files, transfer them back, along with output and error files
                        helpers.move_files_back(self._job.id,
                                                self.get_job_description(),
                                                self.get_saga_session())
                        # Update last status
                        self._job.last_status = val
                        if self._job not in db.session:
                            db.session.merge(self._job)
                        current_app.logger.debug('Before commit the new value is %s ' % val)
                        db.session.commit()
                    if val in (saga.FAILED,
                               saga.DONE,
                               saga.CANCELED,
                               saga.FINAL,
                               saga.EXCEPTION):
                        print 'Breaking ...', val
                        return
                except saga.IncorrectState:
                    pass
        g = gevent.spawn(monitor_state)

        # Check our job's id and state
        self._logger.debug("Job ID    : %s" % self._saga_job.id)
        self._logger.debug("Job State : %s" % self._saga_job.state)

        # Run the job eventually
        self._logger.debug("...starting job...")
        self._saga_job.run()

        # Store remote pid
        self._job.remote_pid = self._saga_job.get_id()
        db.session.commit()

        self._logger.debug("Job ID    : %s" % self._saga_job.id)
        self._logger.debug("Job State : %s" % self._saga_job.state)

        # TODO: Where should I close job service properly? I should put it in user session or g?
        #self._job_service.close()

    def get_job_description(self):
        """
        Returns job description object
        """
        return self._job_description

    def cancel(self):
        """
        Cancel the job
        """
        if self._job.remote_pid:
            self._saga_job.cancel()
            # self._job.status = self._saga_job.state
            # db.session.commit()
        else:
            raise JobManagerException('Job PID unknown')

