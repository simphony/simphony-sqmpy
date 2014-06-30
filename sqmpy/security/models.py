"""
    sqmpy.security.models
    ~~~~~~~~~~~~~~~~

    User related database models
"""
import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import SmallInteger
from sqlalchemy.orm import relationship, backref

from sqmpy.database import Base
from sqmpy.security import constants

__author__ = 'Mehdi Sadeghi'


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    password = Column(String(120))
    role = Column(SmallInteger, default=constants.USER)
    status = Column(SmallInteger, default=constants.NEW)
    registered_on = Column(DateTime)
    #jobs = relationship("Job", backref="users")

    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password
        self.registered_on = datetime.datetime.now()

    def get_status(self):
        return constants.STATUS[self.status]

    def get_role(self):
        return constants.ROLE[self.role]

    def is_authenticated(self):
        return True

    def is_active(self):
        if self.status != constants.INACTIVE:
            return True
        return False

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.name
