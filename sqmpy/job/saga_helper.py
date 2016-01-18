"""
    sqmpy.job.saga_helper
    ~~~~~

    Provides ways to interact with saga classes
"""
import os
import pwd
import time
import base64
import hashlib
from threading import Thread

import saga
import flask
from flask.ext.login import current_user

from . import helpers
from .helpers import send_state_change_email
from .constants import FileRelation, ScriptType, HPCBackend
from .exceptions import JobManagerException
from .models import StagingFile, Job
from .callback import JobStateChangeCallback
from ..database import db

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
        if not flask.current_app.config.get('LOGIN_DISABLED') and\
                flask.current_app.config.get('SSH_WITH_LOGIN_INFO'):
            # Do not load default security contexts (user ssh keys)
            session = saga.Session(False)
            ctx = saga.Context('userpass')
            ctx.user_id = current_user.username
            ctx.user_pass =\
                base64.b64decode(flask.session['password'].decode('utf-8'))
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

        # Register call backs. SAGA callbacks are not reliable and
        # we don't use them unless they are fixed first. Instead,
        # we use a monitoring thread. The flask.copy_current_request_context
        # decorator is very important here, if not used, the other
        # thread will not have access to the context data of the original
        # one.
        # self._register_callbacks()
        # TODO: My monitoring approach is messy and should be changed.
        @flask.copy_current_request_context
        def monitor_state(app):
            with app.app_context():
                while True:
                    flask.current_app.logger.debug(
                        'Monitoring job %s for changes...' % self._job.id)
                    # Check for changes every three seconds
                    time.sleep(3)
                    try:
                        val = self._saga_job.state
                        if val != self._job.last_status:
                            # Shout out load
                            # Todo: use signals here
                            send_state_change_email(self._job.id,
                                                    self._job.owner_id,
                                                    self._job.last_status,
                                                    val,
                                                    silent=True)

                            # Currently storing history is unused.
                            # Insert history record
                            # history_record = JobStateHistory()
                            # history_record.change_time =\
                            #     datetime.datetime.now()
                            # history_record.old_state = self._job.last_status
                            # history_record.new_state = val
                            # history_record.job_id = self._job.id
                            # db.session.add(history_record)
                            # db.session.flush()

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

        # Run the job eventually
        flask.current_app.logger.debug("...starting job[%s]..." % self._job.id)
        self._saga_job.run()

        # Store remote pid
        self._job.remote_job_id = self._saga_job.get_id()
        db.session.commit()

        # Make sure to start monitoring after starting the job
        flask.current_app.logger.debug(
            'creating monitoring thread and passing %s to it' %
            (flask.current_app._get_current_object()))
        thr = Thread(target=monitor_state,
                     args=[flask.current_app._get_current_object()])
        thr.start()

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


def _get_remote_home(session):
    """
    Return homde directory on target resource based on
    the current security context.
    """
    user_id = None
    for ctx in session.list_contexts():
        if ctx.type == 'userpass':
            return '/home/{0}'.format(ctx.user_id)
        elif ctx.type == 'ssh':
            user_id = ctx.user_id

    # If user_id is not in the session object consider the user which
    # is running the application
    # This might not work on Windows, not tried.
    user_id = pwd.getpwuid(os.getuid()).pw_name
    if not user_id:
        import getpass
        user_id = getpass.getuser()
    if not user_id:
        raise Exception("Can't find the right username for SSH connection.")
    return '/home/{0}'.format(user_id)


def get_job_endpoint(job_id, session):
    """
    Returns the remote job working directory. Creates the parent
    folders if they don't exist.
    :param job_id: job id
    :param session: saga session to be used
    :return:
    """
    job = Job.query.get(job_id)
    # We use a combination of job id and a random string to make the
    # directory name unique and meanwhile human readable
    # Use the staging directory name as remote directory name as well,
    # otherwise decide for a new unique name
    # however since directories normally resied on different machines we
    # don't need to do that. It only makes things more human.
    dir_name = None
    if job.staging_dir:
        # Get the last part of path, i.e. job directory. See os.path.split
        if job.staging_dir.endswith('/'):
            dir_name = os.path.split(job.staging_dir[:-1])[-1]
        else:
            dir_name = os.path.split(job.staging_dir)[-1]
    else:
        # If staging directory is not set make a random name
        dir_name = "{0}_{1}".format(job_id,
                                    base64.urlsafe_b64encode(os.urandom(6)))

    if not job.remote_dir:
        job.remote_dir =\
            '{home_directory}/.sqmpy/{path}'.format(
                home_directory=_get_remote_home(session),
                path=dir_name)
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


def download_job_files(job_id, job_description, session, wipe=True):
    """
    Copies output and error files along with any other output files back to the
    current machine.
    :param job_id: job id
    :param job_description:
    :param session: saga session to remote resource
    :param wipe: if set to True will wipe files from remote machine.
    :return:
    """
    # Get staging file names for this job which are already uploaded
    # we don't need to download them since we have them already
    staged_files = \
        StagingFile.query.filter(StagingFile.parent_id == Job.id,
                                 Job.id == job_id).all()
    # Convert tuple result to list
    excluded = [os.path.join(sf.location, sf.name) for sf in staged_files]

    # Get or create job directory
    job_staging_folder = helpers.get_job_staging_folder(job_id)

    # Get the working directory instance
    remote_dir = get_job_endpoint(job_id, session)

    # Find all files in the working directory and its subdirectories
    # Files are as a dict of full_path/saga.filesystem.Url objects
    remote_files, sub_direcotires = _traverse_directory(remote_dir)

    # Copy/move files and create corresponding records in db
    # Note: we can recursively move everything back but the reason
    # behind traversing through all directories is that we want to
    # collect some information about them upon adding.
    for remote_abspath, remote_url in remote_files.iteritems():
        # Copy physical file to local directory. Since paths are absolote
        # we need to make them relative to the job's staging folder
        relative_path =\
            _make_relative_path(remote_dir.get_url().get_path(),
                                remote_abspath)
        # Join the relative path and local job staging directory
        local_path =\
            os.path.join('sftp://localhost{job_path}'.format(
                job_path=job_staging_folder), relative_path)
        # No sftp in path
        local_abspath = os.path.join(job_staging_folder, relative_path)

        # Do nothing if the file is already downloaded or belongs
        # to initially uploaded files.
        if local_abspath in excluded:
            flask.current_app.logger.debug('Excluding %s' % local_abspath)
            continue

        if wipe:
            # Move the file and create parents if required
            remote_dir.move(remote_abspath, local_path,
                            saga.filesystem.CREATE_PARENTS)
        else:
            # Copy the file and create parents if required
            remote_dir.copy(remote_abspath, local_path,
                            saga.filesystem.CREATE_PARENTS)

        # Insert appropriate record into db
        sf = StagingFile()
        sf.name = remote_url.path
        sf.original_name = remote_url.path
        sf.location = os.path.dirname(local_abspath)
        sf.relative_path = relative_path.lstrip(os.sep)
        sf.relation = _get_file_relation_to_job(job_description, remote_url)
        sf.checksum = hashlib.md5(open(local_abspath).read()).hexdigest()
        sf.parent_id = job_id
        db.session.add(sf)

    # Persist changes
    db.session.commit()


def _get_file_relation_to_job(job_description, file_url):
    """
    Find if file is stdout, stderr or generated output.
    """
    if file_url.path == job_description.output:
        return FileRelation.stdout.value
    elif file_url.path == job_description.error:
        return FileRelation.stderr.value
    elif file_url.path in job_description.arguments[0]:
        return FileRelation.script.value
    else:
        return FileRelation.output.value


def _make_relative_path(base_path, full_path):
    """
    Strip out the base_path from full_path and make it relative.
    """
    flask.current_app.logger.debug(
        'got base_path: %s and full_path: %s' % (base_path, full_path))
    if base_path in full_path:
        # Get the common prefix
        common_prefix =\
            os.path.commonprefix([base_path, full_path])
        rel_path = full_path[len(common_prefix):]
        # Remove '/' from the beginning
        if os.path.isabs(rel_path):
            rel_path = rel_path[1:]
        return rel_path


def _traverse_directory(directory,
                        collected_files=None,
                        collected_directories=None):
    """
    Walk through subdirectories and collect files.
    :param directory: instance of saga.filesystem.Directory
    """
    if not collected_files:
        collected_files = {}

    if not collected_directories:
        collected_directories = []

    # Find all files in the working directory and its subdirectories
    for entry in directory.list():
        # Add entry only if its a file
        if directory.is_file(entry):
            # Generate full path to each file
            file_path =\
                os.path.join(directory.get_url().get_path(),
                             entry.path)
            collected_files[file_path] = entry
        # Go through sub-directories
        elif directory.is_dir(entry):
            # Fixme: currently saga failes to populate child Urls,
            # therefore we have to fill it manually. See #483 on Github
            # Desired format is like: {scheme}://{host}/{path}/{sub_path}
            path_template =\
                '{scheme}://{host}/{job_dir}/{job_rel_dir}'
            job_staging_folder = directory.get_url().get_path().lstrip(os.sep)
            sub_dir_path =\
                path_template.format(scheme=directory.get_url().get_scheme(),
                                     host=directory.get_url().get_host(),
                                     job_dir=job_staging_folder,
                                     job_rel_dir=entry.path.lstrip(os.sep))
            flask.current_app.logger.debug(
                'Made this path for sub_dir: %s' % sub_dir_path)
            sub_dir = directory.open_dir(sub_dir_path)
            collected_directories.append(sub_dir)
            collected_files, collected_directories =\
                _traverse_directory(sub_dir,
                                    collected_files,
                                    collected_directories)
        else:
            flask.current_app.logger.debug(
                'Omitting non-file and non-directory entry: %s' % entry)
    # Return collected information
    return collected_files, collected_directories


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
        file_wrapper.copy(remote_job_dir.get_url(), saga.filesystem.RECURSIVE)
