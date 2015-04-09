"""
    sqmpy.views
    ~~~~~~~~~~~~~~~

    View functions
"""
from flask import current_app, Blueprint, render_template
from flask.ext.login import login_required

main_blueprint = Blueprint('sqmpy', __name__)

@main_blueprint.route('/', methods=['GET'])
@login_required
def index():
    """
    Index page handler
    """
    return render_template('index.html')

