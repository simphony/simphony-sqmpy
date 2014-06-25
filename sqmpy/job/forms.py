"""
    sqmpy.scheduling.forms
    ~~~~~~~~~~~~~~~~

    Implements job management forms.
"""
from flask.ext.wtf import RecaptchaField
from wtforms import StringField, BooleanField, TextAreaField, FileField, SelectField, validators, Form
from wtforms.validators import Required, EqualTo, Email, Optional

__author__ = 'Mehdi Sadeghi'


class JobSubmissionForm(Form):
    """
    Form to handle job submission.
    """
    title = StringField('Title', [Required(), validators.Length(min=4, max=50)])
    script = TextAreaField('Script', [Required()])
    input = FileField('Input file', [Optional()])
    resource = SelectField('Resource', [Required()])