"""
    sqmpy.job.helpers
    ~~~~~

    Contains functions and classes which ease the other methods rather
    than implementing a feature.
"""
import os
import hashlib
import smtplib
from email.mime.text import MIMEText

from flask.ext.login import current_user

from sqmpy import app, db
from sqmpy.security.models import User
from sqmpy.job.exceptions import JobManagerException, JobNotFoundException, FileNotFoundException
from sqmpy.job.models import Job, StagingFile
from sqmpy.job.constants import FileRelation, ScriptType

__author__ = 'Mehdi Sadeghi'


def send_state_change_email(job_id, old_state, new_state):
    """
    A simple helper class to send smtp email for job state change
    :param job_id: Job id in database
    :param old_state:
    :param new_state:
    :return:
    """
    owner_email = db.session.query(User.email).filter(User.id == Job.owner_id, Job.id == job_id).one()[0]

    try:
        smtp_server = smtplib.SMTP(app.config.get('MAIL_SERVER'))
        # TODO: Add download links for each output file to message.
        message = \
            'Status changed from {old} to {new}'.format(old=old_state,
                                                        new=new_state)
        message = MIMEText(message)
        message['Subject'] = 'Change in job number [{job_id}]'.format(job_id=job_id)
        message['From'] = app.config.get('DEFAULT_MAIL_SENDER')
        message['To'] = owner_email
        smtp_server.sendmail(app.config.get('DEFAULT_MAIL_SENDER'),
                             [owner_email],
                             message.as_string())
        smtp_server.quit()
    except smtplib.SMTPException, ex:
        app.logger.debug("Callback: Failed to send mail: %s" % ex)


class JobFileHandler(object):
    """
    To save input files of the job in appropriate folders and insert records for them.
    """
    @staticmethod
    def save_input_files(job, input_files, script):
        """
        Saves input files of the given job in appropriate folders
        :param job:
        :param input_files: list of (file_name, file_buffer)
        :param script: given script to be run on remote machines
        :return:
        """
        # Get or create job directory
        job_dir = JobFileHandler.get_job_file_directory(job.id)

        # Save staging data before running the job
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/input_files/
        if input_files is not None:
            for file_name, file_buffer in input_files:
                if file_name is not None and file_buffer is not None:
                    #file_uuid = str(uuid.uuid4())
                    #absolute_name = os.path.join(job_dir, file_uuid)
                    absolute_name = os.path.join(job_dir, file_name)
                    f = open(absolute_name, 'wb')
                    # Copy file buffer into destination
                    from shutil import copyfileobj
                    copyfileobj(file_buffer, f, 16384)
                    f.close()
                    sf = StagingFile()
                    sf.name = file_name
                    sf.relation = FileRelation.input.value
                    sf.original_name = file_name
                    sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
                    sf.location = job_dir
                    sf.parent_id = job.id
                    db.session.add(sf)
                else:
                    raise JobManagerException("Invalid file name or path")

        # Save script
        if job.user_script not in (None, ''):
            # Save as python script if the script is in python or shell script if it is shell
            script_extension = ''
            if job.script_type == ScriptType.python.value:
                script_extension = '.py'
            if job.script_type == ScriptType.shell.value:
                script_extension = '.sh'
            file_name = 'job-{job_id}_script{extension}'.format(job_id=job.id,
                                                                extension=script_extension)
            absolute_name = os.path.join(job_dir, file_name)
            f = open(absolute_name, 'wb')
            f.write(script)
            f.close()
            sf = StagingFile()
            sf.name = file_name
            sf.relation = FileRelation.script.value
            sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
            sf.location = job_dir
            sf.parent_id = job.id
            db.session.add(sf)

        # Flush db session
        #db.session.flush()

    @staticmethod
    def get_job_file_directory(job_id, make_sftp_url=False):
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
        job_owner_dir = os.path.join(app.config.get('STAGING_FOLDER'), job_owner.name)
        if not os.path.exists(job_owner_dir):
            os.makedirs(job_owner_dir)
        job_dir = os.path.join(job_owner_dir, str(job_id))
        if not os.path.exists(job_dir):
            os.makedirs(job_dir)
        if make_sftp_url:
            job_dir = 'sftp://localhost{job_dir}'.format(job_dir=job_dir)
        return job_dir

    @staticmethod
    def get_file_location(job_id, file_name):
        """
        Returns the folder of the file
        :param job_id:
        :param file_name:
        :return:
        """
        job = Job.query.get(job_id)
        if job is None:
            raise JobNotFoundException('Job number %s does not exist.' % job_id)
        for f in job.files:
            if f.name == file_name:
                return JobFileHandler.get_job_file_directory(job.id)
        raise FileNotFoundException('Job number %s does not have any file called %s' % (job_id, file_name))