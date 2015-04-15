"""
    config
    ~~~~~
    This module contains configuration keys for the application.
    See http://flask.pocoo.org/docs/config/ for more information.
"""
import os
_basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = '\x94\xb2\xf2</6\xd7+Op\xc5\x97v)\x83\xda\xff)\xd0UD\xd4NB'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'sqmpy.db') + '?check_same_thread=False'

# Logging options
# LOG_FILE = os.path.join(_basedir, 'sqmpy.log')

# Staging options
STAGING_FOLDER = os.path.join(_basedir, 'staging')

# SMTP Configs
MAIL_SERVER = 'iwmcas.iwm.fraunhofer.de'

# Admin email to send job status notifications to, in case login is disabled
ADMIN_EMAIL = 'sade@iwm.fraunhofer.de'


