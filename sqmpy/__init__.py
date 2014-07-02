"""
    sqmpy
    ~~~~~

    A job management web application that makes it easier
    for scientists to submit and monitor jobs to remote
    to remote resources.
    `sqm' stands for Simple Queue Manager.
"""
from flask import Flask
from flask.ext.wtf.csrf import CsrfProtect
from flask.ext.admin import Admin

from sqmpy.database import db_session
from sqmpy.security import security_blueprint
from sqmpy.job import job_blueprint

__author__ = 'Mehdi Sadeghi'


app = Flask(__name__, static_url_path='')
# This one would be used for production, if any
#app.config.from_pyfile('config.py', silent=True)

# Import config module as configs
app.config.from_object('config')

# Override from environment variable
app.config.from_envvar('SQMPY_SETTINGS', silent=True)

# Setup logging.
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(app.config.get('LOG_FILE'))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(file_handler)

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

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()