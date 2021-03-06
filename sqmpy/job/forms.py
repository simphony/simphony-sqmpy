"""
    sqmpy.job.forms
    ~~~~~~~~~~~~~~~~

    Implements job management forms.
"""
from flask_wtf import FlaskForm as Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
import wtforms as wtf

from .constants import HPCBackend

__author__ = 'Mehdi Sadeghi'


class OptionalIfFieldEqualTo(wtf.validators.Optional):
    # a validator which makes a field optional if
    # another field has a desired value

    def __init__(self, other_field_name, value, *args, **kwargs):
        self.other_field_name = other_field_name
        self.value = value
        super(OptionalIfFieldEqualTo, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception(
                'no field named "%s" in form' % self.other_field_name)
        if other_field.data == self.value:
            super(OptionalIfFieldEqualTo, self).__call__(form, field)


class JobSubmissionForm(Form):
    """
    Form to handle job submission.
    """
    script_file = \
        FileField('Script file',
                  validators=[FileRequired(),
                              FileAllowed(['py', 'sh'],
                              'Python and shell scripts only!')])
    input_files = FileField('Input files', [wtf.validators.Optional()])
    # choices will be filled at runtime
    resource = \
        wtf.SelectField('Resource', [wtf.validators.Optional()], coerce=str)
    new_resource = \
        wtf.StringField('New resource URL', [wtf.validators.Optional()])
    working_directory = \
        wtf.StringField('Remote working directory',
                        [wtf.validators.Optional(),
                         wtf.validators.Regexp('^(/)?([^/\0]+(/)?)+$')])
    hpc_backend = \
        wtf.SelectField(
            'HPC Backend',
            validators=[wtf.validators.Optional()],
            choices=[(entry.value, entry.name) for entry in HPCBackend],
            coerce=int)
    queue = wtf.StringField('Queue name',
                            [wtf.validators.Optional(),
                             wtf.validators.Length(min=1, max=150)])
    project = wtf.StringField('Project name',
                              [wtf.validators.Optional(),
                               wtf.validators.Length(min=1, max=150)])
    total_physical_memory = wtf.IntegerField('Total physical memory',
                                             [wtf.validators.Optional()])
    total_cpu_count = \
        wtf.IntegerField('Total number of CPUs',
                         [OptionalIfFieldEqualTo('hpc_backend',
                          HPCBackend.normal.value)])
    spmd_variation = \
        wtf.StringField('SPMD variation',
                        [OptionalIfFieldEqualTo('hpc_backend',
                         HPCBackend.normal.value),
                         wtf.validators.Length(min=1, max=50)])
    walltime_limit = \
        wtf.IntegerField('Walltime limit in minutes',
                         [OptionalIfFieldEqualTo('hpc_backend',
                          HPCBackend.normal.value)])
    description = wtf.TextAreaField('Description', [wtf.validators.Optional()])
    submit = wtf.SubmitField('Submit')
