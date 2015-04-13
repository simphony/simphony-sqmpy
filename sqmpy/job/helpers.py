"""
    sqmpy.job.helpers
    ~~~~~

    Contains functions and classes which ease the other methods rather
    than implementing a feature.
"""
from flask.helpers import url_for
import os
import shutil
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from shutil import copyfileobj

from flask import current_app

from ..models import db
from ..security.models import User
from .exceptions import JobManagerException, JobNotFoundException, FileNotFoundException
from .models import Job, StagingFile
from .constants import FileRelation, ScriptType

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
    owner_email, = db.session.query(User.email).filter(User.id == owner_id).one()
    smtp_server = smtplib.SMTP(mail_config.get('MAIL_SERVER'))
    job_link = ''
    text_message = \
        'Status changed from {old} to {new}'.format(old=old_state,
                                                    new=new_state)

    server_name = mail_config.get('SERVER_NAME')
    port = None
    if server_name and ':' in server_name:
        port = int(server_name.rsplit(':', 1)[1])
        server_name = server_name.rsplit(':', 1)[0]
    else:
        server_name = 'localhost'
        port = 5000
    url = url_for('.detail', job_id=job_id)
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
        job_owner = \
            User.query.filter(User.id == Job.owner_id,
                              Job.id == job_id).first()
        if not config:
            config = current_app.config
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