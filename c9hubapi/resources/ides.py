from flask.ext.restful import Resource

class Ides(Resource):
    def get(self):
        return {'ides': ides}
