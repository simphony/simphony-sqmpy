"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import os
import time
import base64
import datetime
import hashlib

import saga
import flask
import gevent
from flask.ext.login import current_user

import helpers
from ..database import db
from .constants import FileRelation, ScriptType, HPCBackend
from .exceptions import JobManagerException
from .models import StagingFile, JobStateHistory, Job
from .callback import JobStateChangeCallback

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

        # If job has resource_job_id, connect to it
        if job.remote_job_id:
            self._job_service = self.make_job_service(job.resource_endpoint)
            self._saga_job = self._job_service.get_job(job.remote_job_id)
        else:
            # Creating the job service object i.e. the connection
            job.resource_endpoint = \
                get_resource_endpoint(job.resource.url, job.hpc_backend)
            self._job_service = self.make_job_service(job.resource_endpoint)

    def make_job_service(self, endpoint):
        # Create ssh security context
        ctx = None
        session = None
        if flask.current_app.config.get('SSH_WITH_LOGIN_INFO'):
            # Do not load default security contexts (user ssh keys)
            session = saga.Session(False)
            ctx = saga.Context('userpass')
            ctx.user_id = current_user.username
            ctx.user_pass = base64.b64decode(flask.session['password'])
        else:
            session = saga.Session()
            ctx = saga.Context('ssh')

        # Explicitely add the only desired security context
        session.add_context(ctx)
        js = saga.job.Service(endpoint, session=session)
        # TODO: Fix in upstream. Service does not populate adaptor's session.
        js._adaptor._set_session(session)
        return js

    def _register_callbacks(self):
        """
        Register callback functions for the saga job
        :return:
        """
        # This callback will locally store output files and new states in db
        self._saga_job.add_callback(saga.STATE,
                                    JobStateChangeCallback(self._job, self))

    def get_job(self):
        """
        Returns the inner job
        :return:
        """
        return self._job

    def run(self):
        """
        Run the job on remote resource
        :return:
        """
        # Set remote job working directory
        remote_job_dir = \
            get_job_endpoint(self._job.id, self._job_service.get_session())

        # Make sure the working directory is empty
        if remote_job_dir.list():
            raise JobManagerException('Remote directory is not empty')
        flask.current_app.logger.debug('Going to transfer files')
        # transfer job files to remote directory
        transfer_job_files(self._job.id, remote_job_dir,
                           self._job_service.get_session())
        flask.current_app.logger.debug('File transfer done.')
        # Create saga job description
        jd = make_job_description(self._job, remote_job_dir)
        # Create saga job
        self._saga_job = self._job_service.create_job(jd)

        # Register call backs
        # self._register_callbacks()

        # TODO: My monitoring approach is wrong and should be changed.
        # Prepare our gevent greenlet
        @flask.copy_current_request_context
        def monitor_state():
            while True:
                flask.current_app.logger.debug(
                    'Monitoring job %s for changes...' % self._job.id)
                gevent.sleep(3)
                try:
                    val = self._saga_job.state
                    if val != self._job.last_status:
                        # Shout out load
                        helpers.send_state_change_email(self._job.id,
                                                        self._job.owner_id,
                                                        self._job.last_status,
                                                        val,
                                                        silent=True)

                        # Insert history record
                        history_record = JobStateHistory()
                        history_record.change_time = datetime.datetime.now()
                        history_record.old_state = self._job.last_status
                        history_record.new_state = val
                        history_record.job_id = self._job.id
                        db.session.add(history_record)
                        db.session.flush()

                        # If there are new files, transfer them back, along
                        # with output and error files
                        download_job_files(self._job.id,
                                           self._saga_job.description,
                                           self._job_service.get_session())

                        # Update last status
                        self._job.last_status = val
                        if self._job not in db.session:
                            db.session.merge(self._job)
                        db.session.commit()
                    if val in (saga.FAILED,
                               saga.DONE,
                               saga.CANCELED,
                               saga.FINAL,
                               saga.EXCEPTION):
                        return
                except saga.IncorrectState:
                    pass

        # Spawn the coroutine
        gevent.spawn(monitor_state)

        # Run the job eventually
        flask.current_app.logger.debug("...starting job[%s]..." % self._job.id)
        self._saga_job.run()

        # Store remote pid
        self._job.remote_job_id = self._saga_job.get_id()
        db.session.commit()

        flask.current_app.logger.debug(
            "Remote Job ID    : %s" % self._saga_job.id)
        flask.current_app.logger.debug(
            "Remote Job State : %s" % self._saga_job.state)

    def cancel(self):
        """
        Cancel the job
        """
        self._saga_job.cancel()


def get_resource_endpoint(host, hpc_backend):
    """
    Get ssh URI of remote host
    :param host: host to make url for it
    :param hpc_backend: hpc_backend integer value according to HPCBackend enum
    :return:
    """
    # Default SAGA adaptor to ssh
    adaptor = 'ssh'
    if helpers.is_localhost(host):
        adaptor = 'fork'
    elif hpc_backend == HPCBackend.sge.value:
        adaptor = 'sge+ssh'
    return '{adaptor}://{remote_host}'.format(adaptor=adaptor,
                                              remote_host=host)


def get_job_endpoint(job_id, session):
    """
    Returns the remote job working directory. Creates the parent
    folders if they don't exist.
    :param job_id: job id
    :param session: saga session to be used
    :return:
    """
    job = Job.query.get(job_id)
    # Remote working directory will be inside temp folder
    if not job.remote_dir:
        job.remote_dir =\
            '/home/{username}/.sqmpy/{job_id}'.format(
                username=current_user.username,
                job_id=job.id)
    elif not os.path.isabs(job.remote_dir):
        raise Exception('Working directory should be absolute path.')

    adapter = 'sftp'
    if helpers.is_localhost(job.resource.url):
        adapter = 'file'
    adaptor_string = '{adapter}://{remote_host}{working_directory}'

    remote_address = \
        adaptor_string.format(adapter=adapter,
                              remote_host=job.resource.url,
                              working_directory=job.remote_dir)
    # Appropriate folders will be created
    return \
        saga.filesystem.Directory(remote_address,
                                  saga.filesystem.CREATE_PARENTS,
                                  session=session)


def make_job_description(job, remote_job_dir):
    """
    Creates saga job description
    :param job: job instance
    :param remote_job_dir: saga remote job directory instance
    :return:
    """
    script_file = \
        StagingFile.query.filter(
            StagingFile.parent_id == job.id,
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
    if job.script_type == ScriptType.python.value:
        jd.executable = '/usr/bin/python'
    if job.script_type == ScriptType.shell.value:
        jd.executable = '/bin/sh'
    script_abs_path = '{dir}/{file}'.format(dir=remote_job_dir.get_url().path,
                                            file=script_file.name)
    jd.arguments = [script_abs_path]

    jd.output = '{script_name}.out.txt'.format(script_name=script_file.name)
    jd.error = '{script_name}.err.txt'.format(script_name=script_file.name)
    return jd


def download_job_files(job_id, job_description, session, config=None,
                       wipe=True):
    """
    Copies output and error files along with any other output files back to the
    current machine.
    :param job_id: job id
    :param job_description:
    :param session: saga session to remote resource
    :param wipe: if set to True will wipe files from remote machine.
    :return:
    """
    # Get a new object in this session
    job = Job.query.get(job_id)

    # Get or create job directory
    local_job_dir = helpers.get_job_staging_folder(job_id, config)
    if helpers.is_localhost(job.resource.url):
        local_job_dir_url = local_job_dir
    else:
        local_job_dir_url = \
            helpers.get_job_staging_folder(job_id, config, make_sftp_url=True)

    # Get staging file names for this job which are already uploaded
    # we don't need to download them since we have them already
    uploaded_files = \
        StagingFile.query.with_entities(StagingFile.name).filter(
            StagingFile.parent_id == Job.id,
            Job.id == job_id).all()
    # Convert tuple result to list
    uploaded_files = [file_name for file_name, in uploaded_files]
    remote_dir = get_job_endpoint(job_id, session)
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
        sf.original_name = file_url.path
        sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
        sf.location = local_job_dir
        sf.parent_id = job_id
        db.session.add(sf)
    db.session.commit()


def transfer_job_files(job_id, remote_job_dir, session):
    """
    Upload job files to remote resource
    :param job_id: job id
    :param remote_job_dir: saga.filesystem.Directory instance
        of remote job directory
    :param session: saga.Session instance for this transfer
    :return
    """
    # Copy script and input files to remote host
    uploading_files = \
        StagingFile.query.filter(
            StagingFile.parent_id == job_id,
            StagingFile.relation.in_([FileRelation.input.value,
                                      FileRelation.script.value])).all()
    for file_to_upload in uploading_files:
        # If we don't pass correct session object, saga will create default
        # session object which will not reflect correct security context.
        # it would be useful only for a local run and not multi-user run
        # session and remote_job_dir._adaptor.session should be the same
        file_wrapper = \
            saga.filesystem.File('file://localhost/{file_path}'
                                 .format(file_path=file_to_upload.get_path()),
                                 session=session)
        # TODO: This is a workaround for bug #480 remove it later
        file_wrapper._adaptor._set_session(session)
        file_wrapper.copy(remote_job_dir.get_url())
