"""
Entry point for running the sqmpy application standalone
"""
import os
from gevent import monkey; monkey.patch_all()
from sqmpy.factory import create_app

# This line added to support heroku deployment
port = int(os.environ.get("PORT", 3000))
app = create_app('../config.py')
app.run(port=port)
