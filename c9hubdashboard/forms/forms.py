import os
from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length


class BaseForm(Form):
    pass


class CreateIdeForm(BaseForm):
    display_name = StringField('Display name', validators=[DataRequired(), Length(min=1, max=64)], default='toto')
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=32)], default='toto')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=32)], default='toto')
    git_clones = StringField('Git clones', validators=[DataRequired()], default='https://github.com/mk-fg/layered-yaml-attrdict-config.git https://github.com/kmike/port-for.git')
