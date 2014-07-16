"""
    sqmpy.scheduling.forms
    ~~~~~~~~~~~~~~~~

    Implements job management forms.
"""
from flask.ext.wtf import Form
#from flask.ext.wtf.html5 import URLField
from wtforms import StringField, TextAreaField, FileField, SelectField, validators

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
    script = TextAreaField('Script', [validators.Required()])
    input_file = FileField('Input file', [validators.Optional()])
    # choices will be filled at runtime
    resource = SelectField('Resource', [validators.Required()], coerce=int)
    description = TextAreaField('Description', [validators.Optional()])
    #url = URLField(validators=[validators.url()])