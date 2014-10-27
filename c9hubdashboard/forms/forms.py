import os
from flask_wtf import Form
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, StopValidation


class BaseForm(Form):
    pass


def is_cf_enabled(form, field):
    if not form.setup_cf.data:
        # clear out processing errors
        field.errors[:] = []
        # Stop further validators running
        raise StopValidation()


class CreateIdeForm(BaseForm):
    display_name = StringField('Display name', validators=[DataRequired(), Length(min=1, max=64)])
    timeout = SelectField(u'Timeout', choices=[('15m', '15 minutes'), ('1h', '1 hour'), ('2h', '2 hours'), ('3h', '3 hours')], default="15m")
    git_clones = StringField('Git clones', validators=[DataRequired()], default='https://github.com/mcowger/hello-python.git')
    setup_cf = BooleanField('CloudFoundry')
    cf_api_endpoint = StringField('Api endpoint', validators=[is_cf_enabled, DataRequired()], default='https://api.cfapps.tailab.eu')
    cf_username = StringField('Username', validators=[is_cf_enabled, DataRequired()], default='')
    cf_password = PasswordField('Password', validators=[is_cf_enabled, DataRequired(), Length(min=1, max=64)], default='')
    cf_org = StringField('Organization', validators=[is_cf_enabled, DataRequired()], default='ideaas-test-project')
    cf_spc = StringField('Space', validators=[is_cf_enabled, DataRequired()], default='dev')
