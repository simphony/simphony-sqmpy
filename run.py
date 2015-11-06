"""
Entry point for running the sqmpy application standalone
"""
import os
from gevent import monkey
monkey.patch_all()
from sqmpy.factory import create_app

# This line added to support heroku deployment
port = int(os.environ.get("PORT", 3000))

# Workaround for passing ssh options to underlying library. Since we want
# to avoid any question upon ssh initialization, therefore we have tp add
# this StrictHostKeyChecking=no to ~/.ssh/config, otherwise we will get
# an error when connecting to new host, since there is no way currently to
# pass this option programmatically.

# Pass the correct config file and create the app instance
app = create_app('../config.py')

# If pyOpenSSL is installed it is possible to use adhoc certificates:
# app.run(host='0.0.0.0', port=port, ssl_context='adhoc')
app.run(host='0.0.0.0', port=port, ssl_context=('server.crt', 'server.key'))
