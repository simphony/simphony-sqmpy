__author__ = 'Mehdi Sadeghi'

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqmpy.database import Base


class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    title = Column(String(50), unique=False)
    submit_date = Column(DateTime, unique=False)
    status = Column(String(50), unique=False)
    input_location = Column(String(200), unique=False)
    output_location = Column(String(200), unique=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    program_id = Column(Integer, ForeignKey('programs.id'))
    queue_id = Column(Integer, ForeignKey('queues.id'))


class Program(Base):
    __tablename__ = 'programs'
    id = Column(Integer, primary_key=True)
    title = Column(String(50), unique=False)
    executable = Column(String(100), unique=True)
    jobs = relationship("Job", backref="programs")


class Queue(Base):
    __tablename__ = 'queues'
    id = Column(Integer, primary_key=True)
    title = Column(String(50), unique=False)
    type_id = Column(Integer, ForeignKey('queuetypes.id'))
    host = Column(String(150), unique=False)
    jobs = relationship("Job", backref="queues")


class QueueType(Base):
    __tablename__ = 'queuetypes'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    queues = relationship("Queue", backref="queuetypes")
