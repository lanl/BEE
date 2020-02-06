# Fifo scheduler
# A working mockup of a scheduler

from flask import Flask
from flask_restful import Resource, Api, reqparse, fields

flask_app = Flask(__name__)


class SchedActions(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

api.add_resource(, '/bee_sched/v1/', endpoint = 'sched')
