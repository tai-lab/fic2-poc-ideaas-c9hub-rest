import os
from flask_wtf import Form
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length


class BaseForm(Form):
    pass


class CreateIdeForm(BaseForm):
    display_name = StringField('Display name', validators=[DataRequired(), Length(min=1, max=64)])
    timeout = SelectField(u'Timeout', choices=[('15m', '15 minutes'), ('1h', '1 hour'), ('2h', '2 hours'), ('3h', '3 hours')], default="15m")
    git_clones = StringField('Git clones', validators=[DataRequired()], default='https://github.com/mcowger/hello-python.git')
