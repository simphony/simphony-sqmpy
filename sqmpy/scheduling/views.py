__author__ = 'Mehdi Sadeghi'

from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from sqmpy import admin
from sqmpy.database import db_session
import sqmpy.scheduling.models

# Adding appropriate admin views
admin.add_view(ModelView(sqmpy.scheduling.models.Job, db_session))
admin.add_view(ModelView(sqmpy.scheduling.models.Program, db_session))
admin.add_view(ModelView(sqmpy.scheduling.models.Queue, db_session))