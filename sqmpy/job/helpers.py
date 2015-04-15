"""
    sqmpy.job.helpers
    ~~~~~

    Contains functions and classes which ease the other methods rather
    than implementing a feature.
"""
import os
import time
import shutil
import hashlib
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from shutil import copyfileobj

import saga
from flask import current_app
from flask.ext.login import current_user
from flask.helpers import url_for

from ..models import db
from ..security.models import User
from .exceptions import JobManagerException, JobNotFoundException, FileNotFoundException
from .models import Job, StagingFile
from .constants import FileRelation, ScriptType, Adaptor

__author__ = 'Mehdi Sadeghi'


def send_state_change_email(job_id, owner_id, old_state, new_state, mail_config=None):
    """
    A simple helper class to send smtp email for job state change
    :param job_id: Job id in database
    :param owner_id: job's owner id
    :param old_state:
    :param new_state:
    :return:
    """
    if not mail_config:
        mail_config = current_app.config

    if owner_id:
        owner_email, = db.session.query(User.email).filter(User.id == owner_id).one()
    elif 'ADMIN_EMAIL' in mail_config:
        owner_email = mail_config.get('ADMIN_EMAIL')
    else:
        raise Exception('Job owner email unknown.')
    smtp_server = smtplib.SMTP(mail_config.get('MAIL_SERVER'))
    text_message = \
        'Status changed from {old} to {new}'.format(old=old_state,
                                                    new=new_state)

    server_name = mail_config.get('SERVER_ADDRESS')
    if server_name and ':' in server_name:
        port = int(server_name.rsplit(':', 1)[1])
        server_name = server_name.rsplit(':', 1)[0]
    else:
        server_name = 'localhost'
        port = 5000
    url = url_for('.detail', job_id=job_id)
    if not port or port == 80:
        job_link = 'http://{host_name}{url}'.format(host_name=server_name,
                                                    url=url)
    else:
        job_link = 'http://{host_name}:{port}{url}'.format(host_name=server_name,
                                                           port=port,
                                                           url=url)

    html_message = \
        """<DOCTYPE html>
        <html>
        <head></head>
        <body>
             <h3>Job status change alert</h3>
             <p>
             {text_message}

             <a href="{link}">Job #{job_id} detail page</a>
             </p>
        </body>
        </html>""".format(text_message=text_message,
                          job_id=job_id,
                          link=job_link)

    part1 = MIMEText(text_message, 'plain')
    part2 = MIMEText(html_message, 'html')

    message = MIMEMultipart('alternative')
    message.attach(part1)
    message.attach(part2)
    message['Subject'] = 'State changed in job #{job_id}'.format(job_id=job_id)
    message['From'] = mail_config.get('DEFAULT_MAIL_SENDER')
    message['To'] = owner_email
    smtp_server.sendmail(mail_config.get('DEFAULT_MAIL_SENDER'),
                         [owner_email],
                         message.as_string())
    smtp_server.quit()


def get_resource_endpoint(host, adaptor):
    """
    Get ssh URI of remote host
    :param host: host to make url for it
    :param adaptor: adaptor integer value according to Adaptor enum
    :return:
    """
    backend = 'ssh'
    if is_localhost(host):
        backend = 'fork'
    elif adaptor == Adaptor.sge.value:
        backend = 'sge+ssh'
    return '{backend}://{remote_host}'.format(backend=backend,
                                              remote_host=host)


def is_localhost(host):
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
        job.remote_dir = '/tmp/sqmpy/{job_id}'.format(job_id=job.id)
    adapter = 'sftp'
    if is_localhost(job.resource.url):
        adapter = 'file'
    remote_address = \
        '{adapter}://{remote_host}/{working_directory}'.format(adapter=adapter,
                                                               remote_host=job.resource.url,
                                                               working_directory=job.remote_dir)
    # Appropriate folders will be created
    return \
        saga.filesystem.Directory(remote_address,
                                  saga.filesystem.CREATE_PARENTS,
                                  session=session)


def move_files_back(job_id, job_description, session, config=None, wipe=True):
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
    local_job_dir = JobFileHandler.get_job_file_directory(job_id, config)
    if is_localhost(job.resource.url):
        local_job_dir_url = local_job_dir
    else:
        local_job_dir_url = JobFileHandler.get_job_file_directory(job_id, config, make_sftp_url=True)

    # Get staging file names for this job which are already uploaded
    # we don't need to download them since we have them already
    uploaded_files = \
        StagingFile.query.with_entities(StagingFile.name).filter(StagingFile.parent_id == Job.id,
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


class JobFileHandler(object):
    """
    To save input files of the job in appropriate folders and insert records for them.
    """
    @staticmethod
    def make_staging_file_entry(job_id, job_dir, relation, file_name, file_contents, is_buffer=True):
        """
        Create an staging file entity
        :param job_id: job id
        :param job_dir: job directory
        :param relation: type of given file, input, error or script
        :param file_name: file name
        :param file_contents: either a buffer or
        :param is_buffer: is the file_content a buffer or text contents
        :return:
        """
        absolute_name = os.path.join(job_dir, file_name)
        f = open(absolute_name, 'wb')
        if is_buffer:
            # Copy file buffer into destination
            copyfileobj(file_contents, f, 16384)
        else:
            f.write(file_contents)
        f.close()
        sf = StagingFile()
        sf.name = file_name
        sf.relation = relation
        sf.original_name = file_name
        sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
        sf.location = job_dir
        sf.parent_id = job_id

        return sf

    @staticmethod
    def stage_uploaded_files(job, upload_dir, config, silent=False):
        """
        Saves files in the given directory under the given job's directory
        :param job:
        :param upload_dir: a directory containing files prefixed with `input_' and `script_'
        :param silent: skip empty file names
        :return:
        """
        # Get or create job directory
        job_dir = JobFileHandler.get_job_file_directory(job.id, config)

        # Save staging data before running the job
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/input_files/
        for filename in os.listdir(upload_dir):
            staging_file_name = None
            if filename.startswith('input_'):
                staging_file_name = filename[6:]
                staging_file_relation = FileRelation.input.value
            elif filename.startswith('script_'):
                # We rename script file name to avoid collision with input files
                staging_file_name = 'job_{job_id}_{filename}'.format(job_id=job.id,
                                                                     filename=filename[7:])
                staging_file_relation = FileRelation.script.value
                # fill job.script
                job.user_script = open(os.path.join(upload_dir, filename)).read()
                if filename.endswith('.py'):
                    job.script_type = ScriptType.python.value
                if filename.endswith('sh'):
                    job.script_type = ScriptType.shell.value
            elif not silent:
                raise JobManagerException("Invalid file name or path")

            # Move file to job directory
            src = os.path.join(upload_dir, filename)
            dst = os.path.join(job_dir, staging_file_name)
            shutil.move(src, dst)

            # Create a record for each file
            sf = StagingFile()
            sf.name = staging_file_name
            sf.relation = staging_file_relation
            sf.original_name = filename
            sf.checksum = hashlib.md5(open(dst).read()).hexdigest()
            sf.location = job_dir
            sf.parent_id = job.id
            db.session.add(sf)
        # Delete temporary upload directory
        os.removedirs(upload_dir)
        db.session.flush()

    @staticmethod
    def get_job_file_directory(job_id, config=None, make_sftp_url=False):
        """
        Returns the directory which contains job files

        :param job_id:
        :param make_sftp_url: return as sftp address
        :return: file system path
        :rtype : str
        """
        if not config:
            config = current_app.config

        if current_user.is_anonymous:
            # Use the username which this process is running under it
            import getpass
            job_owner_dir = os.path.join(config.get('STAGING_FOLDER'), getpass.getuser())
        else:
            job_owner = \
                User.query.filter(User.id == Job.owner_id,
                                  Job.id == job_id).first()
            job_owner_dir = os.path.join(config.get('STAGING_FOLDER'), job_owner.username)

        if not os.path.exists(job_owner_dir):
            os.makedirs(job_owner_dir)
        job_dir = os.path.join(job_owner_dir, str(job_id))
        if not os.path.exists(job_dir):
            os.makedirs(job_dir)
        if make_sftp_url:
            job_dir = 'sftp://localhost{job_dir}'.format(job_dir=job_dir)
        return job_dir

    @staticmethod
    def get_file_location(job_id, file_name, config=None):
        """
        Returns the folder of the file
        :param job_id:
        :param file_name:
        :return:
        """
        # If there is a request context get the config
        if current_app != None:
            config = current_app.config
        job = Job.query.get(job_id)
        if job is None:
            raise JobNotFoundException('Job number %s does not exist.' % job_id)
        for f in job.files:
            if f.name == file_name:
                return JobFileHandler.get_job_file_directory(job.id, config)
        raise FileNotFoundException('Job number %s does not have any file called %s' % (job_id, file_name))