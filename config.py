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

# Staging options
STAGING_FOLDER = os.path.join(_basedir, 'staging')

# SMTP Configs
MAIL_SERVER = 'iwmcas.iwm.fraunhofer.de'

# Default web server address. Set this to whatever address the server will run
# This will be used to generate urls outside of a request context for example
# for notifications which contain links to certain pages such as job details.
#SERVER_NAME = 'sqmpy.iwm.fraunhofer.de:3000'

# Admin email to send job status notifications to, in case login is disabled
ADMIN_EMAIL = 'sade@iwm.fraunhofer.de'


