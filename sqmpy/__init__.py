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

__author__ = 'Mehdi Sadeghi'


app = None
db = None


class SqmpyApplication(Flask):
    """
    To wrap sqmpy stuff
    """
    def __init__(self):
        super(SqmpyApplication, self).__init__(__name__, static_url_path='')

        # Import config module as configs
        self.config.from_object('config')

        # Override from environment variable
        self.config.from_envvar('SQMPY_SETTINGS', silent=True)

        # Initialize db right after basic initialization
        self.db = SQLAlchemy(self)

        self._configure_logging()

        # Activate other apps
        CsrfProtect(self)
        self.admin = Admin(self)
#        self.mail = Mail(self)


    def _configure_logging(self):
        """
        Logging settings
        """
        # Setup logging.
        import logging
        from logging import Formatter
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(self.config.get('LOG_FILE'))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        self.logger.addHandler(file_handler)

    def register_admin_views(self):
        """
        Register admin views from different modules.
        """
        # Add security admin views
        from sqmpy.security import models as security_models
        self.admin.add_view(ModelView(security_models.User, self.db.session))

        # Adding job admin views
        from sqmpy.job import models as job_models
        self.admin.add_view(ModelView(job_models.Job, self.db.session))
        self.admin.add_view(ModelView(job_models.Resource, self.db.session))
        self.admin.add_view(ModelView(job_models.JobStateHistory, self.db.session))

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