"""
    sqmpy.job.helpers
    ~~~~~

    Contains functions and classes which ease the other methods rather
    than implementing a feature.
"""
import os
import base64
import shutil
import hashlib
import smtplib
import socket
from threading import Thread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import flask
from flask import url_for
from flask.ext.login import current_user

from ..database import db
from ..security import manager as security_services
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
        mail_config = flask.current_app.config

    if not mail_config.get('NOTIFICATION'):
        return

    owner_email = None
    if owner_id:
        print security_services.get_user(owner_id).id
        owner_email = security_services.get_user(owner_id).email
    elif 'ADMIN_EMAIL' in mail_config:
        owner_email = mail_config.get('ADMIN_EMAIL')

    if not owner_email:
        raise Exception('Job owner email unknown.')

    text_message = \
        'Status changed from {old} to {new}'.format(old=old_state,
                                                    new=new_state)
    job_link = None
    if flask.current_app is not None:
        with flask.current_app.app_context():
            # `jobs` is name of the corresponding blueprint
            job_link = url_for('jobs.detail',
                               job_id=job_id,
                               _external=True)
    else:
        job_link = url_for('jobs.detail',
                           job_id=job_id,
                           _external=True)

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

    try:
        thr = Thread(target=send_async_mail,
                     args=[mail_config.get('SMTP_HOST', 'localhost'),
                           mail_config.get('SMTP_PORT', 0),
                           mail_config.get('DEFAULT_MAIL_SENDER'),
                           [owner_email],
                           message.as_string()])
        thr.start()
    except Exception, error:
        flask.current_app.logger.debug(
            "Callback: Failed to send mail: %s" % error)
        if not silent:
            raise


def send_async_mail(host, port, fromaddr, toaddrs, msg):
    smtp_server = smtplib.SMTP(host, port)
    smtp_server.sendmail(fromaddr,
                         toaddrs,
                         msg)
    smtp_server.quit()


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
    if not job.staging_dir:
        job.staging_dir = get_job_staging_folder(job.id, config)

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
        dst = os.path.join(job.staging_dir, staging_file_name)
        shutil.move(src, dst)

        # Create a record for each file
        sf = StagingFile()
        sf.name = staging_file_name
        sf.relation = staging_file_relation
        sf.original_name = filename
        sf.checksum = hashlib.md5(open(dst).read()).hexdigest()
        sf.location = job.staging_dir
        sf.parent_id = job.id
        db.session.add(sf)
    # Delete temporary upload directory
    os.removedirs(upload_dir)
    db.session.flush()


def get_job_staging_folder(job_id, config=None):
    """
    Returns the directory which contains job files

    :param job_id:
    :return: file system path
    :rtype : str
    """
    # Check if the job has alreday a staging directory
    job = Job.query.get(job_id)
    if job.staging_dir:
        return job.staging_dir

    if not config:
        config = flask.current_app.config

    staging_dir = config.get('STAGING_DIR', flask.current_app.instance_path)

    if current_user.is_anonymous:
        # Use the username which this process is running under it
        job_owner_dir = os.path.join(staging_dir, 'anonymous_user')
    else:
        job_owner = \
            security_services.get_user(job.owner_id)
        # Use job owner's username as top level directory for
        # his/her jobs
        job_owner_dir = os.path.join(staging_dir, job_owner.username)
    # Create a directory for the user if it does not exist yet
    if not os.path.exists(job_owner_dir):
        os.makedirs(job_owner_dir)

    # We use a combination of job id and a random string to make the
    # directory name unique and meanwhile human readable
    dir_name = "{0}_{1}".format(job_id,
                                base64.urlsafe_b64encode(os.urandom(6)))
    job_path = os.path.join(job_owner_dir, dir_name)
    if not os.path.exists(job_path):
        os.makedirs(job_path)
    return job_path
