"""
Entry point for running the sqmpy application standalone
"""
import os

#from gevent import monkey; monkey.patch_all()

from sqmpy import create_app

if __name__ == '__main__':
    """
    Run application directly. Some samples:
        app.run(host='localhost', port=5001)
        # port will be read from SERVER_NAME or will be 5000
        app.run(host='localhost')
        # host will be 127.0.0.1
        # port will be read from SERVER_NAME or will be 5000
        app.run()

        # Pleae note that SERVER_NAME is used for subdomains only and has no effect here.
    """
    # This line added to support heroku deployment
    port = int(os.environ.get("PORT", 5001))
    app = create_app('../config.py')
    app.run(host='0.0.0.0', port=port)
