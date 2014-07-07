"""
    sqmpy.job.models
    ~~~~~~~~~~~~~~~~

    Job related database models
"""
import os

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, backref

from sqmpy.database import Base
from sqmpy.job.constants import FileRelation

__author__ = 'Mehdi Sadeghi'


class Job(Base):
    """
    A job represents a task submitted by user to a remote resource.
    """
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    submit_date = Column(DateTime)
    last_status = Column(String(50))
    remote_pid = Column(Integer)
    user_script = Column(Text())
    description = Column(Text())
    owner_id = Column(Integer, ForeignKey('users.id'))
    resource_id = Column(Integer, ForeignKey('resources.id'))
    files = relationship('StagingFile')


class Resource(Base):
    """
    Each resource represents a cluster, remote server or a computer which
    is accessible at least with SSH
    """
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    url = Column(String(150), unique=True)
    jobs = relationship('Job', backref="resource")


class StagingFile(Base):
    """
    This entity will keep track of files for each job, either input or output.
    """
    __tablename__ = 'stagingfiles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    original_name = Column(String(50))
    relation = Column(Integer, nullable=False)
    location = Column(String(150), nullable=False)
    checksum = Column(String)
    parent_id = Column(Integer, ForeignKey('jobs.id'))

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


# class Program(Base):
#     __tablename__ = 'programs'
#     id = Column(Integer, primary_key=True)
#     title = Column(String(50), unique=False)
#     executable = Column(String(100), unique=True)


# class Queue(Base):
#     __tablename__ = 'queues'
#     id = Column(Integer, primary_key=True)
#     title = Column(String(50), unique=False)
#     type_id = Column(Integer, ForeignKey('queuetypes.id'))
#     host = Column(String(150), unique=False)
#     jobs = relationship("Job", backref="queues")


# class QueueType(Base):
#     __tablename__ = 'queuetypes'
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100), unique=True)
#     queues = relationship("Queue", backref="queuetypes")