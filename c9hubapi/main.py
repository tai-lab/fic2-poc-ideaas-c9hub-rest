from flask import Flask, request
from flask.ext.restful import Resource, Api

from c9hubapi.resources.ides import Ides
from c9hubapi.resources.ide import Ide

app = Flask(__name__)
api = Api(app)


ides = {}


class _Ides(Resource):
    def get(self):
        return {'ides': ides}


class _Ide(Resource):
    def get(self, ide_id):
        if (ide_id in ides):
            return {'ide_id': ides[ide_id]}
        else:
            return {'error': "Unknown ide_id '%s'" % ide_id}, 404

    def post(self, ide_id):
        ides[ide_id] = request.form['data']
        return {'ide_id': ides[ide_id]}



api.add_resource(_Ides, '/v1/ide')
api.add_resource(_Ide, '/v1/ide/<string:ide_id>')

def main():
    app.debug = True
    app.run(debug=True, host='0.0.0.0', port=3232)

if __name__ == '__main__':
    main()
