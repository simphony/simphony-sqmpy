"""
    config
    ~~~~~
    This module contains configuration keys for the application.
    Setting these keys, you can override default values.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
import os

# Statement for enabling the development environment
# DEBUG = True

# Define the secret key for signing session cookies.
# For every installation this should be unique. This will be used to
# encrypt cookies.
SECRET_KEY = "This string will be replaced with a proper key in production."

# Get current directory
_basedir = os.path.abspath(os.path.dirname(__file__))

# Define the database URI.
SQLALCHEMY_DATABASE_URI =\
    'sqlite:///' + os.path.join(_basedir,
                                'data.db')

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "this will be replaced with a strong secret"

# Sqmpy uses this directory as file storage. All scripts, input and output
# files will be stored at subfolders at this directory, separated by
# usernames and job IDs.
#STAGING_DIR = '/tmp/sqmpy/staging'

# Set to True to get notifications (emails) when status of submitted job changes.
#NOTIFICATION = False

# Mail server settings. Change these to point to your smtp mail server.
#SMTP_HOST = 'localhost'
#SMTP_PORT = 25
#DEFAULT_MAIL_SENDER = 'noreply@sqmpy.local'

# Default web server address. Set this to whatever address the server will run
# This will be used to generate urls outside of a request context, for example
# for notifications which contain links to certain pages such as job details.
# This is important to generate URL in background threads.
# SERVER_NAME = 'pc-p282.iwm.fraunhofer.de:3000'

# By default login is disabled. Enable it for a central setup
LOGIN_DISABLED = True

# User user login information for SSH. This has no meaning if login is disabled.
# TODO: remove this flag. It is confusing. Instead, provide a per-host connection
# settings for each user.
SSH_WITH_LOGIN_INFO = False

# Enables LDAP login and will cause LDAP credentials to be used for SSH as well.
# TODO: use authentication backends instead of this flag. Remove this.
USE_LDAP_LOGIN = False
#LDAP_SERVER = 'ldap.example.com'
#LDAP_BASEDN = 'ou=People,ou=IWM,o=Fraunhofer,c=DE'
DEBUG = True
