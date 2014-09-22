import sys
from flask import Flask, g
from flask.ext.restful import Api
from c9hubapi.resources import ides
from c9hubapi.db import models
from pkg_resources import resource_stream
import lya


cfg = lya.AttrDict.from_yaml(resource_stream('c9hubapi.resources.etc', 'c9hub.default.yaml'))
print(' * Configuration ...')
cfg.dump(sys.stdout)

app = Flask(__name__)
api = Api(app)


@app.before_request
def before_request():
    g.session = models.session()
    g.cfg = cfg

@app.teardown_request
def teardown_request(exception):
    session = getattr(g, 'session', None)
    if session is not None:
        session.close()

api.add_resource(ides.Ides, '/v1/ide')
api.add_resource(ides.Ide, '/v1/ide/<string:ide_id>')
api.add_resource(ides.IdeRedirect, '/v1/ide/<string:ide_id>/redirect')
