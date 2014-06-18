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

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from sqmpy.database import db_session
from sqmpy.communication.constants import COMMUNICATION_MANAGER
from sqmpy.communication.channels.ssh import SSHFactory

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

# Enabling views
import sqmpy.views
import sqmpy.security.views
import sqmpy.scheduling.views

#Instanciate core and services manually
# look at http://flask.pocoo.org/docs/api/#flask.Flask.logger
#app.logger.debug("Importing core..")
import sqmpy.core
from sqmpy.core import core_services
import sqmpy.communication

# Getting communication manager in order to add SSH channel.
# Right now these are not dynamic but later on I will make them
# dynamic if we need to. So far I make the code more flexible
# to let future changes happen simpler.
import communication.services as communication_services

# Adding the only supported channel so far. SSH
communication_services.register_factory(SSHFactory())


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
