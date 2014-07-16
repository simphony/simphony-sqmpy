"""
    sqmpy.job.models
    ~~~~~~~~~~~~~~~~

    Job related database models
"""
import os
import datetime

from sqmpy import db
from sqmpy.job.constants import FileRelation

__author__ = 'Mehdi Sadeghi'


class Job(db.Model):
    """
    A job represents a task submitted by user to a remote resource.
    """
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    submit_date = db.Column(db.DateTime)
    last_status = db.Column(db.String(50))
    remote_pid = db.Column(db.Integer)
    user_script = db.Column(db.Text())
    description = db.Column(db.Text())
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'))
    files = db.relationship('StagingFile')

    def __init__(self,
                 name=None,
                 owner_id=None,
                 resource_id=None,
                 user_script=None,
                 sub_date=None,
                 description=None):
        self.name = name
        self.owner_id = owner_id
        self.resource_id = resource_id
        self.user_script = user_script
        if sub_date is None:
            sub_date = datetime.datetime.utcnow()
        self.submit_date = sub_date
        self.description = description

    def __repr__(self):
        return '<Job %s>' % self.id


class Resource(db.Model):
    """
    Each resource represents a cluster, remote server or a computer which
    is accessible at least with SSH
    """
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    url = db.Column(db.String(150), unique=True)
    jobs = db.relationship('Job', backref="resource")

    # I pass None to params to let Admin page to create objects
    def __init__(self, name=None, url=None):
        self.name = name
        self.url = url

    def __repr__(self):
        return '<Resource %s>' % self.url


class StagingFile(db.Model):
    """
    This entity will keep track of files for each job, either input or output.
    """
    __tablename__ = 'stagingfiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    original_name = db.Column(db.String(50))
    relation = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    checksum = db.Column(db.String)
    parent_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))

    def get_path(self):
        """
        Full path to file
        :return:
        """
        return os.path.join(self.location, self.name)

    def get_relation_str(self):
        """
        Return string representation for relation value
        :return:
        """
        return FileRelation(self.relation).name.lower()
        #FileRelation.tostring(self.relation)

    def __repr__(self):
        return '<File %s>' % self.name


class JobStateHistory(db.Model):
    """
    Record of changes in job state
    """
    __tablename__ = 'jobstatehistory'
    id = db.Column(db.Integer, primary_key=True)
    # Please note that real change time would be a little different,
    # because there is a time interval that we query about status changes
    change_time = db.Column(db.DateTime)
    old_state = db.Column(db.String(50))
    new_state = db.Column(db.String(50))
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))

    def __repr__(self):
        return '<State from %s to %s>' % (self.old_state, self.new_state)