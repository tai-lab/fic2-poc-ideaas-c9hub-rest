import sys, logging, uuid
from flask import Flask, g
from flask.ext.restful import Api
from flask.ext.login import LoginManager, UserMixin
from c9hubapi.resources import ides, validation_endpoints
from c9hubapi.db import models
from pkg_resources import resource_stream
import lya
import requests, http, json, uuid


#logging.basicConfig(level=logging.DEBUG)
http.client.HTTPConnection.debuglevel = 1
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.addHandler(logging.StreamHandler())

cfg = lya.AttrDict.from_yaml(resource_stream('c9hubapi.resources.etc', 'c9hub.default.yaml'))
print(' * Configuration ...')
cfg.dump(sys.stdout)

app = Flask(__name__, template_folder='../templates')
#app.secret_key = 'secret_sqdusdh'
app.config['SESSION_PROTECTION'] = None

models._register_validation_endpoints(cfg.validation_endpoints)
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)



class OAuthUser(UserMixin):
    def __init__(self, id, target_endpoint_id):
        self.id = str(id)
        self.target_endpoint_id = target_endpoint_id

# @login_manager.user_loader
# def load_user(userid):
#     return OAuthUser(userid)
    
@login_manager.request_loader
def load_user_from_request(request):
    app.logger.info("load_user_from_request !")
    bearer = request.headers.get('Authorization', None)
    if bearer is None or not bearer.startswith('Bearer '):
        return None
    try:
        validation_endpoint_uuid = uuid.UUID(request.headers.get('Validation-Endpoint', None))
    except ValueError:
        return None
    this_session = models.session()
    target_endpoint = this_session.query(models.ValidationEndpoint).filter_by(uuid=validation_endpoint_uuid).first()
    if target_endpoint is None:
        return None
    target_url = target_endpoint.url
    target_id = target_endpoint.id
    this_session.close()
    if '{}' in target_url:
        access_token = bearer[len('Bearer '):]
        r = requests.get(target_url.format(access_token),
                         verify=False)
    else:
        r = requests.get(target_url,
                         verify=False,
                         headers={'Authorization': bearer,
                                  'Content-Type': 'application/json'})
    if r.status_code == 200:
        try:
            if not str(r.json()['id']):
                raise ValueError()
            id = str(r.json()['id'])
            return OAuthUser(id, target_id)
        except (ValueError, KeyError) as _:
            app.logger.error("load_user_from_request: invalid parsing of the user id")
    return None

@app.before_request
def before_request():
    g.session = models.session()
    g.cfg = cfg

@app.teardown_request
def teardown_request(exception):
    session = getattr(g, 'session', None)
    if session is not None:
        session.close()

api.add_resource(validation_endpoints.ValidationEndpoints, '/v1/validationendpoint')
api.add_resource(ides.Ides, '/v1/ide')
api.add_resource(ides.Ide, '/v1/ide/<string:ide_id>')
api.add_resource(ides.IdeRedirect, '/v1/ide/<string:ide_id>/redirect')
