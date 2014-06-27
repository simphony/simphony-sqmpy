from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, PasswordField, BooleanField
from wtforms.validators import Required, EqualTo, Email, Optional


class LoginForm(Form):
    """
    A basic login form.
    """
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])


class RegisterForm(Form):
    """
    A basic registration form.
    """
    name = TextField('Name', [Required()])
    email = TextField('Email', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Repeat Password', [
        Required(),
        EqualTo('password', message='Passwords must match')
    ])
    #accept_tos = BooleanField('I accept the TOS', [Optional()])
    #recaptcha = RecaptchaField([Required()])