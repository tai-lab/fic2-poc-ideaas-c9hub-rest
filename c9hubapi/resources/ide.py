from flask.ext.restful import Resource

class Ide(Resource):
    def get(self, ide_id):
        if (ide_id in ides):
            return {'ide_id': ides[ide_id]}
        else:
            return {'error': "Unknown ide_id '%s'" % ide_id}, 404

    def post(self, ide_id):
        ides[ide_id] = request.form['data']
        return {'ide_id': ides[ide_id]}
