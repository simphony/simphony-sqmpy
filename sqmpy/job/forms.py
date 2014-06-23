"""
    sqmpy.scheduling.forms
    ~~~~~~~~~~~~~~~~

    Implements job management forms.
"""
from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, BooleanField, TextAreaField, FileField, SelectField
from wtforms.validators import Required, EqualTo, Email, Optional

__author__ = 'Mehdi Sadeghi'


class JobSubmissionForm(Form):
    """
    Form to handle job submission.
    """
    title = TextField('Title', [Required()])
    script = TextAreaField('Script', [Required()])
    input = FileField('Input file', [Optional()])
    resources = SelectField('Resources', [Required()])