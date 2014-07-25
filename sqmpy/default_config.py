"""
    default_config
    ~~~~~~~~~~~~~~
    This module contains configuration keys for the application.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
import os
import tempfile
#_basedir = os.path.abspath(os.path.dirname(__file__))


DEBUG = False

# Server host and port. Supports subdomains myapp.dev:5000
# SERVER_NAME = '0.0.0.0:5001'

ADMINS = frozenset(['sade@iwm.fraunhofer.de'])
SECRET_KEY = "This string will be replaced with a proper key in production."

SQLALCHEMY_DATABASE_URI = 'sqlite:///'
DATABASE_CONNECT_OPTIONS = {}

THREADS_PER_PAGE = 8

CSRF_ENABLED = True
CSRF_SESSION_KEY = "somethingimpossibletoguess"

# Recaptcha for localhost
RECAPTCHA_USE_SSL = False
RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
RECAPTCHA_OPTIONS = {'theme': 'white'}


# Logging options
LOG_FILE = None#os.path.join(_basedir, 'sqmpy.log')

# Staging options
STAGING_FOLDER = tempfile.gettempdir()

# SMTP Configs
MAIL_SERVER = 'localhost'
DEFAULT_MAIL_SENDER = 'monitor@sqmpy'

PER_PAGE = 20