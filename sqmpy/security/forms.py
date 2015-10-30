"""
    sqmpy.security.forms
    ~~~~~~~~~~~~~~~~

    Implements security forms.
"""
from flask.ext.wtf import Form
from wtforms import PasswordField, StringField, validators


class LoginForm(Form):
    """
    A basic login form.
    """
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])


class RegisterForm(Form):
    """
    A basic registration form.
    """
    validate_message = 'Only alphanumeric values between 3-16 characters'
    username = \
        StringField('Username',
                    [validators.DataRequired(),
                     validators.Regexp('^[a-z0-9_-]{3,16}$',
                     message=validate_message)])
    password = PasswordField('Password', [validators.DataRequired()])
    email = \
        StringField('Email', [validators.DataRequired(), validators.Email()])
    confirm = PasswordField('Repeat Password', [
        validators.DataRequired(),
        validators.EqualTo('password', message='Passwords must match')
    ])
