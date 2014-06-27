"""
    sqmpy
    ~~~~~

    A job management web application that makes it easier
    for scientists to submit and monitor jobs to remote
    to remote resources.
    `sqm' stands for Simple Queue Manager.
"""
import os
import sys

from flask import Flask, Blueprint
from flask.ext.wtf.csrf import CsrfProtect
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from sqmpy.database import db_session
from sqmpy.communication.constants import COMMUNICATION_MANAGER
from sqmpy.communication.channels.ssh import SSHFactory
from sqmpy.job import job_blueprint
from sqmpy.security import security_blueprint

__author__ = 'Mehdi Sadeghi'

app = Flask(__name__, static_url_path='')
# This one would be used for production, if any
#app.config.from_pyfile('config.py', silent=True)

# Import config module as configs
app.config.from_object('config')

# Override from environment variable
app.config.from_envvar('SQMPY_SETTINGS', silent=True)

#Enabling Admin app
admin = Admin(app)

# Enable CSRF protection
CsrfProtect(app)

# Registering blueprints,
# IMPORTANT: views should be imported before registering blueprints
import sqmpy.views
import sqmpy.security.views
import sqmpy.job.views
app.register_blueprint(security_blueprint)
app.register_blueprint(job_blueprint)

#Instanciate core and services manually
# look at http://flask.pocoo.org/docs/api/#flask.Flask.logger
#app.logger.debug("Importing core..")
import sqmpy.core
import sqmpy.communication
#from sqmpy.core import core_services

# Getting communication manager in order to add SSH channel.
# Right now these are not dynamic but later on I will make them
# dynamic if we need to. So far I make the code more flexible
# to let future changes happen simpler.
#import communication.services as communication_services

# Adding the only supported channel so far. SSH
#communication_services.register_factory(SSHFactory())


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

