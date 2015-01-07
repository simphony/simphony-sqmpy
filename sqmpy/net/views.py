"""
    sqmpy
    ~~~~~

    This file is part of sqmpy project.
"""
from flask import request, session, g, redirect, url_for, abort, \
    render_template, flash, send_from_directory
from flask.ext.login import login_required, current_user
from flask.ext.csrf import csrf_exempt

from sqmpy.net import net_blueprint

__author__ = 'Mehdi Sadeghi'


@net_blueprint.route('/net/', methods=['GET'])
@login_required
def index():
    """
    Entry page for net subsystem
    :return:
    """
    return render_template('net/netmap.html',
                           net={})