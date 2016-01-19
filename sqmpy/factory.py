from flask import Flask
from flask.ext.wtf.csrf import CsrfProtect


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
    from .database import db
    db.init_app(app)

    # Activate CSRF protection
    if app.config.get('CSRF_ENABLED'):
        CsrfProtect(app)

    # Register blueprints
    from .security import security_blueprint
    from .job import job_blueprint
    from .views import main_blueprint
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

    return app
