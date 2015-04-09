"""
    sqmpy.security.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for security module
"""
from flask import flash, url_for, request, redirect, render_template, abort
from flask.ext.login import login_user, logout_user, login_required

from .. import db
from . import security_blueprint
from sqlalchemy.exc import IntegrityError
from .forms import LoginForm, RegisterForm
from .manager import get_password_digest
from .models import User
from . import services as security_services

__author__ = 'Mehdi Sadeghi'


@security_blueprint.route('/security/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    error = None
    if request.method == 'POST':
        # login and validate the user...
        username = request.form.get('username')
        password = request.form.get('password')
        if security_services.valid_login(username, password):
            remember = None
            if request.form.get('remember') is not None:
                remember = True
            user = User.query.filter_by(username=username).one()
            login_user(user, remember=remember)
            flash('Successfully logged in.')
            return redirect(request.args.get('next') or url_for('index'))
        else:
            error = 'Invalid username/password'
    return render_template('security/login.html', form=form, error=error)


@security_blueprint.route('/security/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@security_blueprint.route('/security/register', methods=['GET', 'POST'])
def register():
    """
    Register a new user
    :return:
    """
    form = RegisterForm(request.form, csrf_enabled=False)
    error = None
    if request.method == 'POST':
        if form.validate():
            try:
                user = User(form.username.data,
                            get_password_digest(form.password.data),
                            form.email.data,)
                db.session.add(user)
                db.session.commit()
                # After a successful register log in the user and go to home page.
                login_user(user)
                flash('Successfully registered')
                return redirect('/')
            except IntegrityError:
                error = 'User with similar information already exists'
    return render_template('security/register.html', form=form, error=error)