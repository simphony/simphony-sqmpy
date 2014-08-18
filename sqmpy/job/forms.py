"""
    sqmpy.job.forms
    ~~~~~~~~~~~~~~~~

    Implements job management forms.
"""
from wtforms import StringField, TextAreaField, SelectField, validators

from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField, FileAllowed, FileRequired
#from flask.ext.uploads import UploadSet, IMAGES,SCRIPTS
#from flask.ext.wtf.html5 import URLField

from sqmpy.job.constants import Adaptor

__author__ = 'Mehdi Sadeghi'


class InputFileForm(Form):
    """
    To get list of input files
    """


#scripts = UploadSet('scripts', SCRIPTS)


class JobSubmissionForm(Form):
    """
    Form to handle job submission.
    """
    name = StringField('Name', [validators.DataRequired(), validators.Length(min=1, max=50)])
    script_file = FileField('Script File', validators=[FileRequired(),
                                                       FileAllowed(['py', 'sh'], 'Python and Shell scripts only!')])
    input_files = FileField('Input Files', [validators.Optional()])
    # choices will be filled at runtime
    resource = SelectField('Existing Resource', [validators.Optional()], coerce=str)
    new_resource = StringField('New Resources URL', [validators.Optional()])
    submit_type = SelectField('Submit Type',
                              validators=[validators.Optional()],
                              choices=[(entry.value, entry.name) for entry in Adaptor],
                              coerce=int)
    description = TextAreaField('Description', [validators.Optional()])