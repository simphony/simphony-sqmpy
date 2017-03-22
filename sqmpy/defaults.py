"""
    default_config
    ~~~~~~~~~~~~~~
    This module contains default configuration keys for the application.
    Use a copy of this module to provide custom keys.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
# Set to True to get interactive debug output instead of HTTP 500 error
DEBUG = False

# The secret key will be used to encrypt cookies.
SECRET_KEY = "This string will be replaced with a proper key in production."

# Database settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///'
DATABASE_CONNECT_OPTIONS = {}
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# CSRF settings
CSRF_ENABLED = True
CSRF_SESSION_KEY = "somethingimpossibletoguess"

# Localhost Recaptcha settings
RECAPTCHA_USE_SSL = False
RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
RECAPTCHA_OPTIONS = {'theme': 'white'}

# This folder will hold all user and job produced files, an `staging` directory
# will be created in instance folder in case this is not defined.
# if not provided a staging folder will be created at current directory.
# STAGING_DIR = '/var/sqmpy/staging'

# Will try to send notification emails when job status changes.
NOTIFICATION = False

# Mail settings
SMTP_HOST = 'localhost'
SMTP_PORT = 25
DEFAULT_MAIL_SENDER = 'noreply@sqmpy.local'

# Default web server address. Set this to whatever address the server will run
# This will be used to generate urls outside of a request context, for example
# for notifications which contain links to certain pages such as job details.
# This is important to generate URL in background threads.
# SERVER_NAME = 'sqmpy.example.com:3000'

# By default login is disabled. Enable it for a central setup
LOGIN_DISABLED = True

# TODO: remove this flag. It is confusing. Instead.
# TODO: instead, provide a per-host connection settings for each user.
# Use user login information for SSH. Default option is password-less access.
# When set, sqmpy will use the provided username and password to obtain a
# SSH connection to any remote host. Otherwise, passwordless SSH access will
# be assumed, i.e. the user running sqmpy, should have passwor-less SSH access
# to any given remote machine.
SSH_WITH_LOGIN_INFO = False

# Enables LDAP login, will cause LDAP credentials to be used for SSH as well.
# TODO: use authentication backends instead of this flag. Remove this.
USE_LDAP_LOGIN = False
LDAP_SERVER = 'localhost'
# For example: LDAP_BASEDN = 'ou=People,ou=IWM,o=Fraunhofer,c=DE'
LDAP_BASEDN = ''

# Number of results to show when using pagination
PER_PAGE = 10

# Default CSRF
#WTF_CSRF_CHECK_DEFAULT = False