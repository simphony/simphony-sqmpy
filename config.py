import os
_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

ADMINS = frozenset(['sade@iwm.fraunhofer.de'])
SECRET_KEY = "This string will be replaced with a proper key in production."

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'sqmpy.db')
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
LOG_FILE = os.path.join(_basedir, 'sqmpy.log')

# Staging options
STAGING_FOLDER = os.path.join(_basedir, 'staging')

# SMTP Configs, uncomment any line to add it
#TODO Right now only MAIL_SERVER is being read, fix others.
MAIL_SERVER = 'iwmcas.iwm.fraunhofer.de'
DEFAULT_MAIL_SENDER = 'sade@iwm.fraunhofer.de'
#MAIL_SERVER = default 'localhost'
#MAIL_PORT = 25
#MAIL_USE_TLS = False
#MAIL_USE_SSL = False
#MAIL_DEBUG = app.debug
#MAIL_USERNAME = 'sade'
#MAIL_PASSWORD = 'tvhki,tv'
#DEFAULT_MAIL_SENDER = None