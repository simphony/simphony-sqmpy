"""
    default_config
    ~~~~~~~~~~~~~~
    This module contains configuration keys for the application.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
import tempfile

DEBUG = True

SECRET_KEY = "This string will be replaced with a proper key in production."

SQLALCHEMY_DATABASE_URI = 'sqlite:///'
DATABASE_CONNECT_OPTIONS = {}

THREADS_PER_PAGE = 8

CSRF_ENABLED = False
CSRF_SESSION_KEY = "somethingimpossibletoguess"

# Recaptcha for localhost
RECAPTCHA_USE_SSL = False
RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
RECAPTCHA_OPTIONS = {'theme': 'white'}

# If replaced with a file address, app will log there.
# LOG_FILE = None

# Staging options
STAGING_FOLDER = tempfile.gettempdir()

# SMTP Configs
MAIL_SERVER = 'localhost'
DEFAULT_MAIL_SENDER = 'monitor@sqmpy'

# Number of results to show at each page
PER_PAGE = 10

# Redis URL
REDISTOGO_URL = 'redis://localhost:6379'

# For first release there is no login-procedure
LOGIN_DISABLED = True