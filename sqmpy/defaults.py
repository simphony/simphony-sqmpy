"""
    default_config
    ~~~~~~~~~~~~~~
    This module contains configuration keys for the application.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
DEBUG = True

# To sign cookies
SECRET_KEY = "This string will be replaced with a proper key in production."

# Database settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///'
DATABASE_CONNECT_OPTIONS = {}

# CSRF settings
CSRF_ENABLED = False
CSRF_SESSION_KEY = "somethingimpossibletoguess"

# Localhost Recaptcha settings
RECAPTCHA_USE_SSL = False
RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
RECAPTCHA_OPTIONS = {'theme': 'white'}

# This folder will hold all user and job produced files, an `staging` directory
# will be created in instance folder in case this is not defined.
# STAGING_DIR = '/path/to/staging_dir'

# Mail settings
MAIL_SERVER = 'localhost'
DEFAULT_MAIL_SENDER = 'monitor@sqmpy'

# Number of results to show when using pagination
PER_PAGE = 10

# Redis URL
REDISTOGO_URL = 'redis://localhost:6379'