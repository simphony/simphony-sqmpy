"""
    sqmpy.security.views
    ~~~~~~~~~~~~~~~~~~~~~

    View functions for security module
"""
from flask import flash, url_for, request, redirect, render_template, session
from flask.ext.login import login_user, logout_user, login_required

from ..database import db
from sqlalchemy.exc import IntegrityError
from .forms import LoginForm, RegisterForm
from .manager import get_password_digest
from .models import User
from . import manager as security_services

from flask import Blueprint
from flask.ext.login import LoginManager, AnonymousUserMixin

__author__ = 'Mehdi Sadeghi'


# Create security blueprint
security_blueprint = Blueprint('security', __name__, url_prefix='/security')


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
    login_manager.login_view = '/security/login'
    login_manager.login_message_category = "warning"

    # Set custom anonymous user to return the user which is running the
    #   process.
    def make_anon_user():
        return AnonymousUserMixin()
    login_manager.anonymous_user = make_anon_user

    if 'USE_LDAP_LOGIN' in state.app.config:
        @login_manager.user_loader
        def load_user(username):
            print('Going to load ldap user %s' % username)
            user, dn, entry = security_services._get_ldap_user(username)
            return user
    else:
        @login_manager.user_loader
        def load_user(username):
            print('Going to load normal user %s' % username)
            return security_services._get_user(username)

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
                user = security_services.get_user(username)
                login_user(user, remember=request.form.get('remember'))
                flash('Successfully logged in.')
                return redirect(request.args.get('next') or url_for('sqmpy.index'))
            else:
                flash('Invalid username/password', category='error')
        except Exception, error:
            flash('LDAP Error: %s' % error, category='error')
    return render_template('security/login.html', form=form)


@security_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
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
                # After a successful register log in the user and go to home page.
                login_user(user)
                flash('Successfully registered')
                return redirect('/')
            except IntegrityError:
                error = 'User with similar information already exists'
    return render_template('security/register.html', form=form, error=error)
