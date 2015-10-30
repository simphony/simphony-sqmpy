"""
    sqmpy.job.helpers
    ~~~~~

    Contains functions and classes which ease the other methods rather
    than implementing a feature.
"""
import os
import shutil
import hashlib
import smtplib
import socket
import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import current_app
from flask.ext.login import current_user
from flask.helpers import url_for

from ..database import db
from ..security.models import User
from .exceptions import JobManagerException
from .models import Job, StagingFile
from .constants import FileRelation, ScriptType

__author__ = 'Mehdi Sadeghi'


def send_state_change_email(job_id, owner_id, old_state, new_state,
                            mail_config=None, silent=False):
    """
    A simple helper class to send smtp email for job state change
    :param job_id: Job id in database
    :param owner_id: job's owner id
    :param old_state:
    :param new_state:
    :param silent: suppress errors
    :return:
    """
    if not mail_config:
        mail_config = current_app.config

    if not mail_config.get('NOTIFICATION'):
        return

    if owner_id:
        owner_email, = \
            db.session.query(User.email).filter(User.id == owner_id).one()
    elif 'ADMIN_EMAIL' in mail_config:
        owner_email = mail_config.get('ADMIN_EMAIL')
    else:
        raise Exception('Job owner email unknown.')
    text_message = \
        'Status changed from {old} to {new}'.format(old=old_state,
                                                    new=new_state)
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
                          link=url_for('.detail',
                                       job_id=job_id,
                                       _external=True))

    part1 = MIMEText(text_message, 'plain')
    part2 = MIMEText(html_message, 'html')

    message = MIMEMultipart('alternative')
    message.attach(part1)
    message.attach(part2)
    message['Subject'] = 'State changed in job #{job_id}'.format(job_id=job_id)
    message['From'] = mail_config.get('DEFAULT_MAIL_SENDER')
    message['To'] = owner_email

    try:
        smtp_server = smtplib.SMTP(host=mail_config.get('SMTP_HOST',
                                                        'localhost'),
                                   port=mail_config.get('SMTP_PORT', 0))
        smtp_server.sendmail(mail_config.get('DEFAULT_MAIL_SENDER'),
                             [owner_email],
                             message.as_string())
        smtp_server.quit()
    except Exception, error:
        print "Callback: Failed to send mail: %s" % error
        current_app.logger.debug("Callback: Failed to send mail: %s" % error)
        if not silent:
            raise


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


def stage_uploaded_files(job, upload_dir, config, silent=False):
    """
    Saves files in the given directory under the given job's directory
    :param job:
    :param upload_dir: a directory containing files prefixed with `input_'
        and `script_'
    :param silent: skip empty file names
    :return:
    """
    # Get or create job directory
    job_dir = get_job_staging_folder(job.id, config)

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
            staging_file_name = \
                'job_{job_id}_{filename}'.format(job_id=job.id,
                                                 filename=filename[7:])
            staging_file_relation = FileRelation.script.value
            # fill job.script
            job.script = open(os.path.join(upload_dir, filename)).read()
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


def get_job_staging_folder(job_id, config=None, make_sftp_url=False):
    """
    Returns the directory which contains job files

    :param job_id:
    :param make_sftp_url: return as sftp address
    :return: file system path
    :rtype : str
    """
    if not config:
        config = current_app.config

    staging_dir = config.get('STAGING_DIR', current_app.instance_path)

    if current_user.is_anonymous:
        # Use the username which this process is running under it
        job_owner_dir = os.path.join(staging_dir, getpass.getuser())
    else:
        job_owner = \
            User.query.filter(User.id == Job.owner_id,
                              Job.id == job_id).first()
        job_owner_dir = os.path.join(staging_dir, job_owner.username)

    if not os.path.exists(job_owner_dir):
        os.makedirs(job_owner_dir)
    job_dir = os.path.join(job_owner_dir, str(job_id))
    if not os.path.exists(job_dir):
        os.makedirs(job_dir)
    if make_sftp_url:
        job_dir = 'sftp://localhost{job_dir}'.format(job_dir=job_dir)
    return job_dir
