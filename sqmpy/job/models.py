"""
    sqmpy.job.models
    ~~~~~~~~~~~~~~~~

    Job related database models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, backref
from sqmpy.database import Base

__author__ = 'Mehdi Sadeghi'


class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=False)
    submit_date = Column(DateTime, unique=False)
    last_status = Column(String(50), unique=False)
    input_location = Column(String(200), unique=False)
    output_location = Column(String(200), unique=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    user_script = Column(Text())
    #program_id = Column(Integer, ForeignKey('programs.id'))
    #queue_id = Column(Integer, ForeignKey('queues.id'))
    resource_id = Column(Integer, ForeignKey('resources.id'))
    description = Column(Text())


class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    url = Column(String(150), unique=True)
    jobs = relationship('Job', backref="resource")


# class Program(Base):
#     __tablename__ = 'programs'
#     id = Column(Integer, primary_key=True)
#     title = Column(String(50), unique=False)
#     executable = Column(String(100), unique=True)

#
#
# class Queue(Base):
#     __tablename__ = 'queues'
#     id = Column(Integer, primary_key=True)
#     title = Column(String(50), unique=False)
#     type_id = Column(Integer, ForeignKey('queuetypes.id'))
#     host = Column(String(150), unique=False)
#     jobs = relationship("Job", backref="queues")
#
#
# class QueueType(Base):
#     __tablename__ = 'queuetypes'
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100), unique=True)
#     queues = relationship("Queue", backref="queuetypes")