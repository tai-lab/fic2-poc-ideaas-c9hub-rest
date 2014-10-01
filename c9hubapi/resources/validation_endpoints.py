from flask.ext.restful import Resource, fields, marshal_with, abort
from flask import g, request, current_app, redirect
from flask.ext.login import login_required, current_user
from c9hubapi.db import models
import uuid
import pdb
import re, random
from datetime import timedelta
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from c9hubapi.resources import ides


validation_endpoint_fields = {
    'id': fields.String(attribute='uuid'),
    'url': fields.String,
}


class ValidationEndpoints(ides.ACommon):
    @marshal_with(validation_endpoint_fields)
    def get(self):
        self.log.info("ValidationEndpoints.post()")
        query = self.session.query(models.ValidationEndpoint).all()
        return query
