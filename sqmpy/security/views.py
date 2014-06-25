import datetime

from flask import flash, url_for, request, redirect, render_template, abort
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import login_user, logout_user, login_required

from sqmpy import admin
from sqmpy.security import login_manager, security_blueprint, _get_digest
from sqmpy.security.forms import LoginForm, RegisterForm
from sqmpy.security.models import User
from sqmpy.database import db_session
import sqmpy.security.services as security_services
import sqmpy.security.constants as security_constants


class UserView(ModelView):
    """
    User view for admin interface
    """
    def __init__(self):
        super(UserView, self).__init__(User, db_session)


@security_blueprint.route('/security/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if request.method == 'POST':
        #if form.validate_on_submit():
        # login and validate the user...
        email = request.form.get('email')
        password = request.form.get('password')
        if security_services.valid_login(email, password):
            remember = None
            if request.form.get('remember') is not None:
                remember = True
            user = User.query.filter_by(email=email).one()
            login_user(user, remember=remember)
            flash("Logged in successfully.")
            return redirect(request.args.get('next') or url_for('index'))
        else:
            error = "Invalid username/password"
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
    if request.method == 'POST':
        if form.validate():
            user = User(form.name.data,
                        form.email.data,
                        _get_digest(form.password.data))
            db_session.add(user)
            db_session.commit()
            return redirect('/security/login')

    return render_template('security/register.html', form=form)


#Add admin views
admin.add_view(UserView())