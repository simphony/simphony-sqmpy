"""
    sqmpy.security.forms
    ~~~~~~~~~~~~~~~~

    Implements security forms.
"""
from flask.ext.wtf import Form, RecaptchaField
from wtforms import PasswordField, StringField, validators


class LoginForm(Form):
    """
    A basic login form.
    """
    email = StringField('Email address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired()])


class RegisterForm(Form):
    """
    A basic registration form.
    """
    user_name = StringField('Username', [validators.DataRequired(), validators.Regexp('^[a-z0-9_-]{3,16}$')])
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired()])
    confirm = PasswordField('Repeat Password', [
        validators.DataRequired(),
        validators.EqualTo('password', message='Passwords must match')
    ])
    #accept_tos = BooleanField('I accept the TOS', [Optional()])
    #recaptcha = RecaptchaField([Required()])