"""
Entry point for running the sqmpy application standalone
"""
import os
from sqmpy.factory import create_app

# This is necessary to support Heroku deployment
port = int(os.environ.get("PORT", 5000))

# Pass the correct config file and create the app instance
app = create_app('../config.py')


if __name__ == '__main__':
    # In order to use https, use you can pass in your keys:
    # app.run(ssl_context=('server.crt', 'server.key'))
    # It is possible to configure custom hsot and port:
    # app.run(host='127.0.0.1', port=5000)
    app.run()
