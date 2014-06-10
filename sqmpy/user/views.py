from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from sqmpy import admin
from sqmpy.user.models import User
from sqmpy.database import db_session

admin.add_view(ModelView(User, db_session))