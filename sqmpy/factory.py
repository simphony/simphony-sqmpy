from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

from sqmpy.job.monitor import JobMonitorThread


def create_app(config_filename=None, **kwargs):
    """
    Application factory
    :param config_filename:
    :return:
    """
    # Initialize flask app
    app = Flask(__name__.split('.')[0], static_url_path='')

    # Import default configs
    app.config.from_object('sqmpy.defaults')

    # Configurations
    app.config.from_object('config')

    # Load the given config file
    if config_filename:
        app.config.from_pyfile(config_filename, silent=False)

    # Import from environment
    app.config.from_envvar('SQMPY_SETTINGS', silent=True)

    # Updated with keyword arguments
    app.config.update(kwargs)

    # Register app on db
    from sqmpy.database import db
    db.init_app(app)

    csrf = CSRFProtect()
    # Activate CSRF protection
    if app.config.get('CSRF_ENABLED'):
        csrf.init_app(app)

    # Register blueprints
    from sqmpy.security import security_blueprint
    from sqmpy.job import job_blueprint
    from sqmpy.views import main_blueprint
    app.register_blueprint(security_blueprint)
    app.register_blueprint(job_blueprint)
    app.register_blueprint(main_blueprint)

    if __debug__:
        # create_all should be called after models are imported. In current
        # code they are imported along with blue_print imports above.
        with app.app_context():
            db.create_all()

    # A global context processor for sub menu items
    @app.context_processor
    def make_navmenu_items():
        from flask import url_for
        if job_blueprint.name in app.blueprints:
            return {'navitems': {job_blueprint.name:
                                 url_for('%s.index' % job_blueprint.name)}}
        else:
            return {}

    @app.before_first_request
    def activate_job_monitor():
        thread = JobMonitorThread(kwargs={'app': app})
        app.monitor = thread
        thread.start()

    return app
