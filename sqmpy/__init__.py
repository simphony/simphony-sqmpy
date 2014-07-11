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
from flask.ext.mail import Mail

from sqmpy.database import db_session
from sqmpy.security import security_blueprint
from sqmpy.security.manager import SecurityManager
from sqmpy.job import job_blueprint
from sqmpy.job.manager import JobManager

__author__ = 'Mehdi Sadeghi'


#app = None


class SqmpyApplication(Flask):
    """
    To wrap sqmpy stuff
    """
    def __init__(self):
        super(SqmpyApplication, self).__init__(__name__, static_url_path='')
        #app = Flask(__name__, static_url_path='')
        # This one would be used for production, if any
        #self.config.from_pyfile('config.py', silent=True)

        # Import config module as configs
        self.config.from_object('config')

        # Override from environment variable
        self.config.from_envvar('SQMPY_SETTINGS', silent=True)

        #Enabling Admin app
        self.admin = Admin(self)

        self.mail = Mail(self)

        self._enable_apps()
        self._configure_logging()

        @self.teardown_appcontext
        def shutdown_session(exception=None):
            db_session.remove()

    def _enable_apps(self):
        """
        Enable extra apps such as CSRF protection
        """
        # Enable CSRF protection
        CsrfProtect(self)

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
        from sqmpy.security.views import UserView
        self.admin.add_view(UserView())

        # Adding appropriate admin views
        from flask.ext.admin.contrib.sqla import ModelView
        from sqmpy.job import models as job_models
        self.admin.add_view(ModelView(job_models.Job, db_session))
        self.admin.add_view(ModelView(job_models.Resource, db_session))
        self.admin.add_view(ModelView(job_models.JobStateHistory, db_session))


    def load_blueprints(self):
        """
        Load blueprints
        """
        # Registering blueprints,
        # IMPORTANT: views should be imported before registering blueprints
        import sqmpy.views
        import sqmpy.security.views
        import sqmpy.job.views
        self.register_blueprint(security_blueprint)
        self.register_blueprint(job_blueprint)


def init_app():
    """
    Initializes app variable with Flask application.
    I wrap initialization here to avoid import errors
    :return:
    """
    global app
    app = SqmpyApplication()
    app.load_blueprints()
    app.register_admin_views()

    from sqmpy.core import core_services

    #Register the component in core
    #@TODO: This should be dynamic later
    core_services.register(SecurityManager())

    #Register the component in core
    #TODO: This should be dynamic later
    core_services.register(JobManager())

    return app

app = init_app()