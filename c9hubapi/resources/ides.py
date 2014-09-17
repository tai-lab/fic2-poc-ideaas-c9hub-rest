from flask.ext.restful import Resource, fields, marshal_with, abort
from flask import g, request, current_app
from c9hubapi.db import models
import uuid

class ACommon(Resource):
    def __init__(self):
        self.session = getattr(g, 'session', None)
        self.log = current_app.logger


ide_fields = {
    'display_name': fields.String,
    'id': fields.String(attribute='uuid')
}


class Ide(ACommon):
    @marshal_with(ide_fields)
    def get(self, ide_id):
        self.log.info("Ide.get(ide_id=%s)", ide_id)
        try:
            target = uuid.UUID(ide_id)
        except ValueError as e:
            abort(500, error=str(e))
        query = self.session.query(models.Ide).filter_by(uuid=target).first()
        if (query is not None):
            return query
        else:
            return abort(404, error="Unknown ide_id '%s'" % ide_id)

    def update(self, ide_id):
        self.log.info("Ide.update(ide_id=%s)", ide_id)
        tmp = models.Ide(display_name='tata', uuid=uuid.uuid4())
        self.session.add(tmp)
        self.session.commit()
        return {'ide_id': tmp.id}


class Ides(ACommon):
    def post(self):
        self.log.info("Ides.post()")
        dn = request.json['display_name']
        tmp = models.Ide(display_name=dn, uuid=uuid.uuid4())
        self.session.add(tmp)
        self.session.commit()
        return {'id': tmp.id}

    @marshal_with(ide_fields)
    def get(self):
        self.log.info("Ides.get()")
        query = self.session.query(models.Ide).all()
        return query
