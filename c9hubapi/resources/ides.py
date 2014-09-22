from flask.ext.restful import Resource, fields, marshal_with, abort
from flask import g, request, current_app, redirect
from c9hubapi.db import models
import uuid
import docker
import pdb
import re, random
from jsonschema import validate
from jsonschema.exceptions import ValidationError


class ACommon(Resource):
    def __init__(self):
        self.session = getattr(g, 'session', None)
        self.cfg = getattr(g, 'cfg', None)
        self.log = current_app.logger

    def create_docker(self):
        return docker.Client(base_url='unix://var/run/docker.sock',
                             version='1.14',
                             timeout=10)


ide_fields = {
    'display_name': fields.String,
    'id': fields.String(attribute='uuid'),
    'username': fields.String,
    'password': fields.String,
    'container_id': fields.String,
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

    def delete(self, ide_id):
        self.log.info("Ide.delete(ide_id=%s)", ide_id)
        try:
            target = uuid.UUID(ide_id)
        except ValueError as e:
            abort(500, error=str(e))
        query = self.session.query(models.Ide).filter_by(uuid=target).first()
        docker = self.create_docker()
        docker.stop(query.container_id)
        docker.wait(query.container_id)
        docker.remove_container(query.container_id)
        self.session.delete(query)
        self.session.commit()
        return (None, 204, None)

    # def update(self, ide_id):
    #     self.log.info("Ide.update(ide_id=%s)", ide_id)
    #     tmp = models.Ide(display_name='tata', uuid=uuid.uuid4())
    #     self.session.add(tmp)
    #     self.session.commit()
    #     return {'ide_id': tmp.id}


class IdeRedirect(ACommon):
    def get(self, ide_id):
        self.log.info("Ide.delete(ide_id=%s)", ide_id)
        try:
            target = uuid.UUID(ide_id)
        except ValueError as e:
            abort(500, error=str(e))
        query = self.session.query(models.Ide).filter_by(uuid=target).first()
        docker = self.create_docker()
        try:
            inspection = docker.inspect_container(query.container_id)
            tmp = inspection['NetworkSettings']['Ports']['3131/tcp'][0]['HostPort']
            return redirect('http://{}:{}'.format(self.cfg.public_ip, tmp))
        except KeyError:
            abort(500, {'error': 'Cannot compute redirection link'})
        



_ides_post_request_schema = {
    "type" : "object",
    "properties" : {
        "display_name" : {"type" : "string"},
        "credentials": {
            "type" : "object",
            "properties" : {
                "username" : {"type" : "string"},
                "password" : {"type" : "string"},
                },
            "additionalProperties": False,
            "required": [
                "username",
                "password"
                ]
            }
        },
    "additionalProperties": False,
    "required": [
        "display_name"
        ]
    }


class Ides(ACommon):
    @marshal_with(ide_fields)
    def post(self):
        self.log.info("Ides.post()")
        try:
            validate(request.json, _ides_post_request_schema)
        except ValidationError as e:
            abort(500, error=str(e))
        display_name = request.json['display_name']
        username = request.json.get('credentials',{}).get('username', None)
        password = request.json.get('credentials',{}).get('password', None)

        tmp = models.Ide(display_name=display_name, uuid=uuid.uuid4(), username=username, password=password)
        c = self.create_docker()
        for i in range(0, 9):
            port = 49000 + (i * 100) + random.randint(0, 9)
            env = {"C9PORT": port, "C9PASSWORD": tmp.username, "C9USERNAME": tmp.password}
            container = c.create_container(
                image="tai_c9/cloud9:v0",
                command=None,
                detach=True, environment=env, ports=[port])
            try:
                c.start(container, port_bindings={port: ('0.0.0.0', port)})
                break
            except docker.errors.APIError as e:
                if re.match('Bind for 0.0.0.0:{}'.format(port), str(e)):
                    continue
                else:
                    abort(500, error=str(e))
        else: # only if no break
            abort(500, error="No free port available")
        tmp.container_id = container['Id']
        self.session.add(tmp)
        self.session.commit()
        #pdb.set_trace()
        return tmp

    @marshal_with(ide_fields)
    def get(self):
        self.log.info("Ides.get()")
        tmp = self.create_docker()
        query = self.session.query(models.Ide).all()
        return query
