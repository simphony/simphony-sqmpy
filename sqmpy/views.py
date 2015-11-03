"""
    sqmpy.views
    ~~~~~~~~~~~~~~~

    View functions
"""
from flask import Blueprint, redirect, url_for
from flask.ext.login import login_required

main_blueprint = Blueprint('sqmpy', __name__)


@main_blueprint.route('/', methods=['GET'])
@login_required
def index():
    """
    Index page handler
    """
    # Note: jobs is the name of blueprint not the python package.
    return redirect(url_for('jobs.index'))
