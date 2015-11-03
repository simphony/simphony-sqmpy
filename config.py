"""
    config
    ~~~~~
    This module contains configuration keys for the application.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os
_basedir = os.path.abspath(os.path.dirname(__file__))

# Define the secret key for signing session cookies
SECRET_KEY = '\x94\xb2\xf2</6\xd7+Op\xc5\x97v)\x83\xda\xff)\xd0UD\xd4NB'

# Define the database
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'data.db')

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Staging options
STAGING_DIR = '/tmp/staging/'

# SMTP Configs
MAIL_SERVER = 'iwmcas.iwm.fraunhofer.de'

# Notification flag. If true will try to send notifications (emails) when job
# status changes.
NOTIFICATION = True

# Mail server settings
SMTP_HOST = 'localhost'
SMTP_PORT = 1025

# Default web server address. Set this to whatever address the server will run
# This will be used to generate urls outside of a request context for example
# for notifications which contain links to certain pages such as job details.
# SERVER_NAME = 'sqmpy.iwm.fraunhofer.de:3000'

# Admin email to send job status notifications to, in case login is disabled
ADMIN_EMAIL = 'sade@iwm.fraunhofer.de'

# For first release there is no login-procedure
LOGIN_DISABLED = False

# Enables LDAP login, this will cause LDAP credentials to be
#   used for SSH as well
USE_LDAP_LOGIN = False
LDAP_SERVER = 'iwmnds0.iwm.fraunhofer.de'
LDAP_BASEDN = 'ou=People,ou=IWM,o=Fraunhofer,c=DE'

# User user login information for SSH
SSH_WITH_LOGIN_INFO = True
