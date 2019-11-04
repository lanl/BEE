#!flask/bin/python
from flask import Flask
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
app = Api(app)

class JobsList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                    help='Need a title',
                                    location='json')
        super(JobsList, self).__init__()

    # Submit Job
    def post(self):
        pass

class JobActions(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

    # Query Job
    def get(self, id):
        pass
    
    # Start Job
    def put(self, id):
        pass

    # Cancel Job
    def delete(self, id):
        pass

    # Pause Job
    def patch(self, id):
        pass

api.add_resource(JobActions, '/bee_orc/v1/jobs/<int:id>', endpoint = 'jobs')
api.add_resource(JobsList, '/bee_orc/v1/jobs/', endpoint = 'job')

if __name__ == '__main__':
    app.run(debug=True)
