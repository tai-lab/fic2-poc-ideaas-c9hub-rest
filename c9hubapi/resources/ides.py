from flask.ext.restful import Resource, fields, marshal_with, abort
from flask import g, request, current_app, redirect
from flask.ext.login import login_required, current_user
from c9hubapi.db import models
import os, uuid
import docker
import pdb
import re, random, sys
from datetime import timedelta
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from jinja2 import Template
import base64


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
    'authorizationURL': fields.String,
    'tokenURL': fields.String,
    'callbackURL': fields.String,
    'container_id': fields.String,
    'user_id': fields.String,
    'validation_endpoint_id': fields.String(attribute='validation_endpoint.uuid')
}
def _check_current_user_vs(user_id, validation_endpoint_id):
    return (user_id == current_user.id
            and validation_endpoint_id == current_user.target_endpoint_id)


class Ide(ACommon):
    @marshal_with(ide_fields)
    @login_required
    def get(self, ide_id):
        self.log.info("Ide.get(ide_id=%s)", ide_id)
        try:
            target = uuid.UUID(ide_id)
        except ValueError as e:
            abort(500, error=str(e))
        query = self.session.query(models.Ide).filter_by(uuid=target).first()
        if not _check_current_user_vs(query.user_id, query.validation_endpoint_id):
            return abort(411)
        if (query is not None):
            return query
        else:
            return abort(404, error="Unknown ide_id '%s'" % ide_id)

    @login_required
    def delete(self, ide_id):
        self.log.info("Ide.delete(ide_id=%s)", ide_id)
        try:
            target = uuid.UUID(ide_id)
        except ValueError as e:
            abort(500, error=str(e))
        query = self.session.query(models.Ide).filter_by(uuid=target).first()
        if (query):
            if not _check_current_user_vs(query.user_id, query.validation_endpoint_id):
                return abort(401)
            docker = self.create_docker()
            try:
                inspection = docker.inspect_container(query.container_id)
                docker.stop(query.container_id)
                docker.wait(query.container_id)
                docker.remove_container(query.container_id)
            except:
                self.log.info("Ide.delete except: ", sys.exc_info()[0])
            self.session.delete(query)
            self.session.commit()
            return (None, 204, None)
        else:
            abort(404, error="Unknown ide_id '%s'" % ide_id)

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
        "oauth" : {
            "type" : "object",
            "properties" : {
                "authorizationURL" : { "type" : "string" },
                "tokenURL" : { "type" : "string" },
                "clientID" : { "type" : "string" },
                "clientSecret" : { "type" : "string" },
                "callbackURL" : { "type" : "string" }
                },
            "additionalProperties": False,
            "required": ["authorizationURL", "tokenURL", "clientID",
                         "clientSecret", "callbackURL"]
            },
        "git_clones": {
            "type": "array",
            "items": {
                "type": "string"
                },
            "minItems": 0,
            "uniqueItems": True
            },
        "timeout": {
            "type": "string",
            "pattern": "^[0-9]+([.][0-9]+)?(s|m|h|d)$"
            },
        "cf": {
            "type": "object",
            "properties" : {
                "apiEndpoint" : { "type" : "string" },
                "username" : { "type" : "string" },
                "password" : { "type" : "string" },
                "org" : { "type" : "string" },
                "space" : { "type" : "string" }
                },
            "additionalProperties": False,
            "required": ["apiEndpoint", "username", "password", "org", "space"]
            }
        },
    "additionalProperties": False,
    "required": [
        "display_name"
        ]
    }


def _timeout_to_timedelta(timeout):
    match = re.search(r'^(\d+(?:[.]\d+)?)(s|m|h|d)$', timeout)
    if match and match.group(1) and match.group(2):
        f = float(match.group(1))
        return {'s': timedelta(seconds=f),
                'm': timedelta(minutes=f),
                'h': timedelta(hours=f),
                'd': timedelta(days=f),
                }.get(match.group(2), None)
    else:
        return None
    

class Ides(ACommon):
    @marshal_with(ide_fields)
    @login_required
    def post(self):
        self.log.info("Ides.post() usr={}: {}".format(current_user, request.json))
        try:
            validate(request.json, _ides_post_request_schema)
        except ValidationError as e:
            abort(500, error="Validation error on '{}': {}".format(request.json, str(e)))
        display_name = request.json['display_name']
        authorizationURL = request.json.get('oauth',{}).get('authorizationURL', None)
        tokenURL = request.json.get('oauth',{}).get('tokenURL', None)
        clientID = request.json.get('oauth',{}).get('clientID', None)
        clientSecret = request.json.get('oauth',{}).get('clientSecret', None)
        callbackURL = request.json.get('oauth',{}).get('callbackURL', None)
        timeout = request.json.get('timeout', "15m")
        timeout_delta = _timeout_to_timedelta(timeout)
        if ((timeout_delta) is None) or (timeout_delta > timedelta(hours=4)):
            abort(500, error="Invalid timeout")
        git_clones = ' '.join(request.json.get('git_clones', {}))
        cf_vars = request.json.get('cf', None)

        c = self.create_docker()
        if len(c.containers()) > 8:
            abort(500, error="The limit of concurrently running ides has been reached.")

        tmp = models.Ide(display_name=display_name, uuid=uuid.uuid4(), authorizationURL=authorizationURL,
                         tokenURL=tokenURL, clientID=clientID, clientSecret=clientSecret, callbackURL=callbackURL,
                         user_id=current_user.id, validation_endpoint_id=current_user.target_endpoint_id)
        extra_conf_clear = (current_app.jinja_env.get_template('cloud9_extra_conf.json').render(
            authorizationURL=authorizationURL, tokenURL=tokenURL, clientID=clientID,
            clientSecret=clientSecret, callbackURL=callbackURL,
            validationEndpoint=current_user.target_endpoint_url,
            authorizedId=current_user.id))
        extra_conf_encoded = base64.b64encode(extra_conf_clear.encode('ascii')).decode('ascii')
        env = {"C9PASSWORD": "tmp.password", "C9USERNAME": "tmp.username", "CLONES": git_clones, "C9TIMEOUT": timeout, "C9TRACE": "1", "C9EXTRACONFIG": extra_conf_encoded}
        if (cf_vars):
            env['C9CFEND'] = cf_vars.get('apiEndpoint')
            env['C9CFUSR'] = cf_vars.get('username')
            env['C9CFPASS'] = cf_vars.get('password')
            env['C9CFORG'] = cf_vars.get('org')
            env['C9CFSPC'] = cf_vars.get('space')
        #env = {"CLONES": git_clones, "C9TIMEOUT": timeout}
        try:
            container = c.create_container(
                image="tai_c9/cloud9:v0",
                command=None,
                detach=True, environment=env, ports=[])
            c.start(container, port_bindings={'3131': ('0.0.0.0',)})
            inspection = c.inspect_container(container)
            ip_address = inspection['NetworkSettings']['IPAddress']
        except docker.errors.APIError as e:
            abort(500, error=str(e))

        #content = current_app.jinja_env.get_template('nginx_ide_server.conf').render(id=container['Id'], ip=ip_address)
        #self.log.info('Created nginx location conf: {}'.format(content))
        #a_file=open('/var/tmp/sites-enabled/_ide_{}.conf'.format(container['Id']), 'w+')
        #print(content, file=a_file)
        #a_file.close()
        #if not os.path.exists('/var/tmp/sites-enabled/referers'):
        #    os.makedirs('/var/tmp/sites-enabled/referers')
        #content = current_app.jinja_env.get_template('nginx_ide_referer.conf').render(id=container['Id'], ip=ip_address)
        #self.log.info('Created nginx referer conf: {}'.format(content))
        #a_file=open('/var/tmp/sites-enabled/referers/_ide_{}.conf'.format(container['Id']), 'w+')
        #print(content, file=a_file)
        #a_file.close()

        # for i in c.containers():
        #     #pdb.set_trace()
        #     if '/frontend-nginx' in i['Names']:
        #         self.log.info('Sending HUP signal to {}'.format(i['Id']))
        #         c.kill(i['Id'], signal='HUP')
        #         break
        # else:
        #     self.log.info('The nginx container was not found')

        # for i in range(0, 9):
        #     port = 49000 + (i * 100) + random.randint(0, 9)
        #     env = {"C9PORT": port, "C9PASSWORD": tmp.username, "C9USERNAME": tmp.password, "CLONES": git_clones}
        #     container = c.create_container(
        #         image="tai_c9/cloud9:v0",
        #         command=None,
        #         detach=True, environment=env, ports=[port])
        #     try:
        #         c.start(container, port_bindings={port: ('0.0.0.0', port)})
        #         break
        #     except docker.errors.APIError as e:
        #         if re.match('Bind for 0.0.0.0:{}'.format(port), str(e)):
        #             continue
        #         else:
        #             abort(500, error=str(e))
        # else: # only if no break
        #     abort(500, error="No free port available")

        tmp.container_id = container['Id']
        self.session.add(tmp)
        self.session.commit()
        #pdb.set_trace()
        return tmp

    @marshal_with(ide_fields)
    #@login_required
    def get(self):
        self.log.info("Ides.get()")
        tmp = self.create_docker()
        query = self.session.query(models.Ide).all()
        return query
