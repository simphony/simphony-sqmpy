"""
    sqmpy.views
    ~~~~~~~~~~~~~~~

    View functions
"""
from flask import render_template
from flask.ext.login import login_required

from . import app


@app.route('/', methods=['GET'])
@login_required
def index():
    """
    Index page handler
    """
    return render_template('index.html')

