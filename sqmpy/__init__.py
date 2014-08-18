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
#from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import current_user

from . import default_config

__author__ = 'Mehdi Sadeghi'
__version__ = 'v1.0.0-alpha.4'

app = None
db = None


class SqmpyModelView(ModelView):
    """
    Base admin pages view
    """
    def is_accessible(self):
        return current_user.is_authenticated()


class SqmpyApplication(Flask):
    """
    To wrap sqmpy stuff
    """
    def __init__(self):
        super(SqmpyApplication, self).__init__(__name__.split('.')[0], static_url_path='')

        # Import default configs
        self.config.from_object(default_config)

        # Import config module if exist
        try:
            self.config.from_object('config')
        except ImportError:
            pass

        # Import config file if exists
        self.config.from_pyfile('config.py', silent=True)

        # Override from environment variable if defined
        self.config.from_envvar('SQMPY_SETTINGS', silent=True)

        # Initialize db right after basic initialization
        self.db = SQLAlchemy(self)

        self._configure_logging()

        # Activate other apps
        if self.config.get('CSRF_ENABLED'):
            CsrfProtect(self)

        self.admin = Admin(self)
#        self.mail = Mail(self)

    def _configure_logging(self):
        """
        Logging settings
        """
        import logging
        import sys
        handler = None
        if not self.config.get('LOG_FILE'):
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
        else:
            # Setup logging.
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(self.config.get('LOG_FILE'))
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
        self.logger.addHandler(handler)

    def register_admin_views(self):
        """
        Register admin views from different modules.
        """
        # Add security admin views
        from sqmpy.security import models as security_models
        self.admin.add_view(SqmpyModelView(security_models.User, self.db.session))

        # Adding job admin views
        from sqmpy.job import models as job_models
        self.admin.add_view(SqmpyModelView(job_models.Job, self.db.session))
        self.admin.add_view(SqmpyModelView(job_models.Resource, self.db.session))
        self.admin.add_view(SqmpyModelView(job_models.JobStateHistory, self.db.session))

    def load_blueprints(self):
        """
        Load blueprints
        """
        # Registering blueprints,
        # IMPORTANT: views should be imported before registering blueprints
        import sqmpy.views
        import sqmpy.security.views
        import sqmpy.job.views
        from sqmpy.security import security_blueprint
        from sqmpy.job import job_blueprint

        self.register_blueprint(security_blueprint)
        self.register_blueprint(job_blueprint)

        # If there is no database file, prepare in memory database
        if self.config.get('SQLALCHEMY_DATABASE_URI') == default_config.SQLALCHEMY_DATABASE_URI:
            self.db.create_all()


def __init_app():
    """
    Initializes app variable with Flask application.
    I wrap initialization here to avoid import errors
    :return:
    """
    global app
    app = SqmpyApplication()
    global db
    db = app.db
    app.load_blueprints()
    app.register_admin_views()

    # After loading blueprints create db structure if not exists yet
    app.db.create_all()

    from sqmpy.core import core_services
    from sqmpy.job.manager import JobManager
    from sqmpy.security.manager import SecurityManager

    #Register the component in core
    #@TODO: This should be dynamic later
    core_services.register(SecurityManager())

    #Register the component in core
    #TODO: This should be dynamic later
    core_services.register(JobManager())

    return app


# Initialize app and db
__init_app()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()