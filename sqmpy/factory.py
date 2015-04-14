from flask import Flask
from flask.ext.wtf.csrf import CsrfProtect

from . import default_config


def create_app(config_filename=None, config_dict=None):
    """
    Application factory
    :param config_filename:
    :return:
    """
    # Initialize flask app
    app = Flask(__name__.split('.')[0], static_url_path='')

    # Import default configs
    app.config.from_object(default_config)

    # Import config module from working directory if exists
    try:
        app.config.from_object('config')
    except ImportError:
        pass

    if config_filename:
        # Load the given config file
        app.config.from_pyfile(config_filename)

    # Finally load the given config dictionary and override any existing keys
    if config_dict:
        app.config.update(config_dict)

    # Register app on db
    from .models import db
    db.init_app(app)

    # Activate CSRF protection
    if app.config.get('CSRF_ENABLED'):
        CsrfProtect(app)

    # Registering blueprints,
    # IMPORTANT: views should be imported before registering blueprints
    import sqmpy.views
    import sqmpy.security.views
    import sqmpy.job.views
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
        with app.app_context():
            db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app
