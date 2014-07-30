"""
    sqmpy.scheduling.forms
    ~~~~~~~~~~~~~~~~

    Implements job management forms.
"""
from flask.ext.wtf import Form
#from flask.ext.wtf.html5 import URLField
from wtforms import StringField, TextAreaField, FileField, SelectField, validators
from sqmpy.job.constants import ScriptType

__author__ = 'Mehdi Sadeghi'


class InputFileForm(Form):
    """
    To get list of input files
    """


class JobSubmissionForm(Form):
    """
    Form to handle job submission.
    """
    name = StringField('Name', [validators.Required(), validators.Length(min=1, max=50)])
    script_type = SelectField('Script Type',
                              [validators.AnyOf([e.value for e in ScriptType])],
                              coerce=int,
                              choices=[(e.value, e.name) for e in ScriptType])
    script = TextAreaField('Script', [validators.Required()])
    input_file = FileField('Input file', [validators.Optional()])
    # choices will be filled at runtime
    resource = SelectField('Existing Resource', [validators.Optional()], coerce=str)
    new_resource = StringField('New Resources URL', [validators.Optional()])
    description = TextAreaField('Description', [validators.Optional()])
    #url = URLField(validators=[validators.url()])