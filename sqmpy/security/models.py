"""
    sqmpy.security.models
    ~~~~~~~~~~~~~~~~

    User related database models
"""
import datetime

from ..database import db
from .constants import UserRole, UserStatus

__author__ = 'Mehdi Sadeghi'


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.SmallInteger, default=UserRole.user.value)
    status = db.Column(db.SmallInteger, default=UserStatus.new.value)
    registered_on = db.Column(db.DateTime)

    def __init__(self, username=None, password=None, email=None):
        self.username = username
        self.password = password
        self.email = email
        self.registered_on = datetime.datetime.now()
        self.role = UserRole.user.value
        self.status = UserStatus.new.value

    def get_status(self):
        return UserStatus(self.status)

    def get_role(self):
        return UserRole(self.role)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        if self.status != UserStatus.inactive.value:
            return True
        return False

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.username
