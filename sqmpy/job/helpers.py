"""
    sqmpy.job.helpers
    ~~~~~

    Contains functions and classes which ease the other methods rather
    than implementing a feature.
"""
import os
import hashlib

from flask.ext.login import current_user

from sqmpy.database import db_session
from sqmpy.job.exceptions import JobManagerException, JobNotFoundException, FileNotFoundException
from sqmpy.job.models import Job, StagingFile
from sqmpy.job.constants import FileRelation

__author__ = 'Mehdi Sadeghi'


class JobInputFileHandler(object):
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
        job_dir = JobInputFileHandler._get_job_file_directory(job.id)

        # Save staging data before running the job
        # Input files will be moved under a new folder with this structure:
        #   <staging_dir>/<username>/<job_id>/input_files/
        if input_files is not None:
            for file_name, file_buffer in input_files:
                if file_name is not None and file_buffer is not None:
                    #file_uuid = str(uuid.uuid4())
                    #absolute_name = os.path.join(job_dir, file_uuid)
                    absolute_name = os.path.join(job_dir, file_name)
                    f = open(absolute_name, 'w')
                    # Copy file buffer into destination
                    from shutil import copyfileobj
                    copyfileobj(file_buffer, f, 16384)
                    f.close()
                    sf = StagingFile()
                    sf.name = file_name
                    sf.relation = FileRelation.INPUT
                    sf.original_name = file_name
                    sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
                    sf.location = job_dir
                    sf.parent_id = job.id
                    db_session.add(sf)
                else:
                    raise JobManagerException("Invalid file name or path")

        # Save script
        if job.user_script not in (None, ''):
            file_name = 'job-{job_id}_script'.format(job_id=job.id)
            absolute_name = os.path.join(job_dir, file_name)
            f = open(absolute_name, 'w')
            f.write(script)
            f.close()
            sf = StagingFile()
            sf.name = file_name
            sf.relation = FileRelation.SCRIPT
            sf.checksum = hashlib.md5(open(absolute_name).read()).hexdigest()
            sf.location = job_dir
            sf.parent_id = job.id
            db_session.add(sf)

        # Commit db session
        db_session.commit()

    @staticmethod
    def _get_job_file_directory(job_id):
        """
        Returns the directory which contains job files
        :param job_id:
        :return:
        """
        from sqmpy import app
        user_dir = os.path.join(app.config['STAGING_FOLDER'], current_user.name)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        job_dir = os.path.join(user_dir, str(job_id))
        if not os.path.exists(job_dir):
            os.makedirs(job_dir)
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
                return JobInputFileHandler._get_job_file_directory(job.id)
        raise FileNotFoundException('Job number %s does not have any file called %s' % (job_id, file_name))