"""
    sqmpy.security.models
    ~~~~~~~~~~~~~~~~

    User related database models
"""
import datetime

from ..models import db
from . import constants

__author__ = 'Mehdi Sadeghi'


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.SmallInteger, default=constants.USER)
    status = db.Column(db.SmallInteger, default=constants.NEW)
    registered_on = db.Column(db.DateTime)

    def __init__(self, username=None, password=None, email=None):
        self.username = username
        self.password = password
        self.email = email
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
        return '<User %r>' % self.username
