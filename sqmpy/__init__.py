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
from flask.ext.sqlalchemy import SQLAlchemy

from . import default_config

__author__ = 'Mehdi Sadeghi'
__version__ = 'v0.2'

# Initialize flask app
app = Flask(__name__.split('.')[0], static_url_path='')

# Import default configs
app.config.from_object(default_config)

# Import config module from working directory if exists
try:
    app.config.from_object('config')
except ImportError:
    pass

# Create database
db = SQLAlchemy(app)

# Activate CSRF protection
if app.config.get('CSRF_ENABLED'):
    CsrfProtect(app)

# Registering blueprints,
# IMPORTANT: views should be imported before registering blueprints and
# after initializing app and db objects. Forgive me if it isn't super cool.
import sqmpy.views
import sqmpy.security.views
import sqmpy.job.views

# Register blueprints
from .security import security_blueprint
from .job import job_blueprint
from .views import main_blueprint
app.register_blueprint(security_blueprint)
app.register_blueprint(job_blueprint)
app.register_blueprint(main_blueprint)

# A global context processor for sub menu items
@app.context_processor
def make_navmenu_items():
    if job_blueprint.name in app.blueprints:
        return {'navitems': {job_blueprint.name: job_blueprint.url_prefix}}
    else:
        return {}

# Create every registered model. BTW `create_all' will check for existence of tables before running CREATE queries.
if app.debug:
    db.create_all()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()