"""
    config
    ~~~~~
    This module contains configuration keys for the application.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
import os
_basedir = os.path.abspath(os.path.dirname(__file__))


DEBUG = True

# Server host and port. Supports subdomains myapp.dev:5000
# SERVER_NAME = '0.0.0.0:5001'

# ADMINS = frozenset(['sade@iwm.fraunhofer.de'])
SECRET_KEY = '\x94\xb2\xf2</6\xd7+Op\xc5\x97v)\x83\xda\xff)\xd0UD\xd4NB'
#
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'sqmpy.db')
# DATABASE_CONNECT_OPTIONS = {}
#
# THREADS_PER_PAGE = 8
#
CSRF_ENABLED = True
# CSRF_SESSION_KEY = "somethingimpossibletoguess"

# Recaptcha for localhost
# RECAPTCHA_USE_SSL = False
# RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
# RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
# RECAPTCHA_OPTIONS = {'theme': 'white'}


# Logging options
LOG_FILE = os.path.join(_basedir, 'sqmpy.log')

# Staging options
STAGING_FOLDER = os.path.join(_basedir, 'staging')

# SMTP Configs
MAIL_SERVER = 'iwmcas.iwm.fraunhofer.de'
# DEFAULT_MAIL_SENDER = 'sade@iwm.fraunhofer.de'

# Number of job records per page
PER_PAGE = 5
