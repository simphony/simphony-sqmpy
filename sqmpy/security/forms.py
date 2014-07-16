from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, PasswordField, validators


class LoginForm(Form):
    """
    A basic login form.
    """
    email = TextField('Email address', [validators.Required(), validators.Email()])
    password = PasswordField('Password', [validators.Required()])


class RegisterForm(Form):
    """
    A basic registration form.
    """
    user_name = TextField('Username', [validators.Required(), validators.Regexp('^[a-z0-9_-]{3,16}$')])
    email = TextField('Email', [validators.Required(), validators.Email()])
    password = PasswordField('Password', [validators.Required()])
    confirm = PasswordField('Repeat Password', [
        validators.Required(),
        validators.EqualTo('password', message='Passwords must match')
    ])
    #accept_tos = BooleanField('I accept the TOS', [Optional()])
    #recaptcha = RecaptchaField([Required()])