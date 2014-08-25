"""
    sqmpy.job.forms
    ~~~~~~~~~~~~~~~~

    Implements job management forms.
"""
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField, FileAllowed, FileRequired
#from flask.ext.uploads import UploadSet, IMAGES,SCRIPTS
#from flask.ext.wtf.html5 import URLField

import wtforms as wtf
from wtforms.fields.core import FieldList

from sqmpy.job.constants import Adaptor

__author__ = 'Mehdi Sadeghi'


# class InputFileForm(Form):
#     """
#     To get list of input files
#     """


#scripts = UploadSet('scripts', SCRIPTS)


# class RequiredIf(Required):
#     # a validator which makes a field required if
#     # another field is set and has a truthy value
#     # http://stackoverflow.com/a/8464478/157216
#
#     def __init__(self, other_field_name, *args, **kwargs):
#         self.other_field_name = other_field_name
#         super(RequiredIf, self).__init__(*args, **kwargs)
#
#     def __call__(self, form, field):
#         other_field = form._fields.get(self.other_field_name)
#         if other_field is None:
#             raise Exception('no field named "%s" in form' % self.other_field_name)
#         if bool(other_field.data):
#             super(RequiredIf, self).__call__(form, field)

# class RequiredIfFieldNotEqualTo(wtf.validators.DataRequired):
#     # a validator which makes a field required if
#     # another field is set and has a truthy value
#
#     def __init__(self, other_field_name, value, *args, **kwargs):
#         self.other_field_name = other_field_name
#         self.value = value
#         super(RequiredIfFieldNotEqualTo, self).__init__(*args, **kwargs)
#
#     def __call__(self, form, field):
#         other_field = form._fields.get(self.other_field_name)
#         if other_field is None:
#             raise Exception('no field named "%s" in form' % self.other_field_name)
#         if other_field.data != self.value:
#             super(RequiredIfFieldNotEqualTo, self).__call__(form, field)


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
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if other_field.data == self.value:
            super(OptionalIfFieldEqualTo, self).__call__(form, field)


class JobSubmissionForm(Form):
    """
    Form to handle job submission.
    """
    name = wtf.StringField('Name', [wtf.validators.DataRequired(), wtf.validators.Length(min=1, max=50)])
    script_file = FileField('Script file', validators=[FileRequired(),
                                                       FileAllowed(['py', 'sh'], 'Python and shell scripts only!')])
    input_files = FileField('Input files', [wtf.validators.Optional()])
    # choices will be filled at runtime
    resource = wtf.SelectField('Existing resource', [wtf.validators.Optional()], coerce=str)
    new_resource = wtf.StringField('New resource URL', [wtf.validators.Optional()])
    working_directory = \
        wtf.StringField('Working directory on remote machine', [wtf.validators.Optional(),
                                                                wtf.validators.Regexp('^(/)?([^/\0]+(/)?)+$')])
    adaptor = wtf.SelectField('Submit type',
                              validators=[wtf.validators.Optional()],
                              choices=[(entry.value, entry.name) for entry in Adaptor],
                              coerce=int)
    queue = wtf.StringField('Queue name', [wtf.validators.Optional(),
                                           wtf.validators.Length(min=1, max=150)])
    project = wtf.StringField('Project name', [wtf.validators.Optional(),
                                               wtf.validators.Length(min=1, max=150)])
    total_physical_memory = wtf.IntegerField('Total physical memory', [wtf.validators.Optional()])
    total_cpu_count = wtf.IntegerField('Total number of CPUs',
                                       [OptionalIfFieldEqualTo('adaptor',
                                                               Adaptor.shell.value)])
    #Single Program Multiple Data
    spmd_variation = wtf.StringField('SPMD variation',
                                     [OptionalIfFieldEqualTo('adaptor',
                                                             Adaptor.shell.value),
                                      wtf.validators.Length(min=1, max=50)])
    walltime_limit = wtf.IntegerField('Walltime limit in minutes',
                                      [OptionalIfFieldEqualTo('adaptor',
                                                              Adaptor.shell.value)])
    description = wtf.TextAreaField('Description', [wtf.validators.Optional()])