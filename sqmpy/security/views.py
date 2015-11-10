"""
    sqmpy.security.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for security module
"""
import base64

from flask import flash, url_for, request, redirect, render_template, session,\
    Blueprint
from flask.ext.login import login_user, logout_user, login_required,\
    LoginManager, AnonymousUserMixin

from ..database import db
from sqlalchemy.exc import IntegrityError
from .forms import LoginForm, RegisterForm
from .manager import get_password_digest
from .models import User
from . import manager as security_services

__author__ = 'Mehdi Sadeghi'


# Create security blueprint
security_blueprint = Blueprint('security', __name__)


@security_blueprint.record_once
def on_load(state):
    # Activate Login
    login_manager = login_manager_factory(state)
    login_manager.init_app(state.app)


def login_manager_factory(state):
    """
    Create a login manager accordingly.
    """
    login_manager = LoginManager()
    login_manager.login_view = 'security.login'
    login_manager.login_message_category = "warning"

    # Set custom anonymous user to return the user which is running the
    #   process.
    def make_anon_user():
        return AnonymousUserMixin()
    login_manager.anonymous_user = make_anon_user

    @login_manager.user_loader
    def load_user(user_id):
        return security_services.get_user(user_id)

    return login_manager


@security_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        # login and validate the user...
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            if security_services.validate_login(username, password):
                user = security_services.get_user_by_username(username)
                login_user(user, remember=request.form.get('remember'))
                flash('Successfully logged in.')
                # We need to store password in order to do SSH
                session['password'] = base64.b64encode(password)
                return redirect(request.args.get('next') or
                                url_for('sqmpy.index'))
            else:
                flash('Invalid username/password', category='error')
        except Exception, error:
            flash(error, category='error')
    return render_template('security/login.html', form=form)


@security_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('password', None)
    return redirect('/')


# TODO: Disable registration for LDAP, or better, enable it only if local
@security_blueprint.route('/register', methods=['GET', 'POST'])
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
                # After a successful register log in the user and go
                # to home page.
                login_user(user)
                # We need to store password in order to do SSH
                session['password'] = base64.b64encode(form.password.data)
                flash('Successfully registered and logged in.')
                return redirect(request.args.get('next') or
                                url_for('sqmpy.index'))
            except IntegrityError:
                error = 'User with similar information already exists'
    return render_template('security/register.html', form=form, error=error)
