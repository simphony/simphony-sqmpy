__author__ = 'Mehdi Sadeghi'

import os
import sys

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from sqmpy.database import db_session


app = Flask(__name__, static_url_path='')
# This one would be used for production, if any
#app.config.from_pyfile('config.py', silent=True)

# Import config module as configs
app.config.from_object('config')

# Override from environment variable
app.config.from_envvar('SQMPY_SETTINGS', silent=True)

#Enabling Admin app
admin = Admin(app)

# Enabling views
import sqmpy.views
import sqmpy.security.views
import sqmpy.scheduling.views

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
