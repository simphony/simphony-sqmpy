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
from shutil import copyfileobj

from sqmpy import app, db
from sqmpy.security.models import User
from sqmpy.job.exceptions import JobManagerException, JobNotFoundException, FileNotFoundException
from sqmpy.job.models import Job, StagingFile
from sqmpy.job.constants import FileRelation, ScriptType

__author__ = 'Mehdi Sadeghi'


def send_state_change_email(job_id, owner_id, old_state, new_state):
    """
    A simple helper class to send smtp email for job state change
    :param job_id: Job id in database
    :param owner_id: job's owner id
    :param old_state:
    :param new_state:
    :return:
    """
    owner_email, = db.session.query(User.email).filter(User.id == owner_id).one()

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
    def save_input_files(job, uploaded_files, silent=False):
        """
        Saves input files of the given job in appropriate folders
        :param job:
        :param uploaded_files: list of (file_name, file_buffer, relation)
        :param silent: skip empty file names
        :return:
        """
        files_to_add = []

        # Get or create job directory
        job_dir = JobFileHandler.get_job_file_directory(job.id)

        # Save staging data before running the job
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/input_files/
        script_file = None
        for file_name, file_buffer, relation in uploaded_files:
            if file_name and file_buffer and relation:
                if relation == FileRelation.script:
                    import copy
                    script_filename = file_name
                    script_file_buffer = copy.copy(file_buffer)
                files_to_add.append((relation.value, file_name, file_buffer, True))
            else:
                if not silent:
                    raise JobManagerException("Invalid file name or path")

        # fill job.script
        job.user_script = script_file_buffer.getvalue()
        if script_filename.endswith('.py'):
            job.script_type = ScriptType.python.value
        if script_filename.endswith('sh'):
            job.script_type = ScriptType.shell.value

        # Finally add all files
        for relation, file_name, file_content, is_buffer in files_to_add:
            sf = JobFileHandler.make_staging_file_entry(job.id,
                                                        job_dir,
                                                        relation,
                                                        file_name,
                                                        file_content,
                                                        is_buffer=is_buffer)
            db.session.add(sf)
        db.session.flush()

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