from flask import Flask, g
from flask.ext.restful import Api
from c9hubapi.resources import ides
from c9hubapi.db import models

app = Flask(__name__)
api = Api(app)


@app.before_request
def before_request():
    g.session = models.session()

@app.teardown_request
def teardown_request(exception):
    session = getattr(g, 'session', None)
    if session is not None:
        session.close()

api.add_resource(ides.Ides, '/v1/ide')
api.add_resource(ides.Ide, '/v1/ide/<string:ide_id>')
