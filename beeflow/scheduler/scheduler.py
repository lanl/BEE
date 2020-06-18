#!/usr/bin/env python3
import os
import sys
import math

from flask import Flask, jsonify, make_response, request
from flask_restful import Resource, Api, reqparse

flask_app = Flask(__name__)
api = Api(flask_app)

# TODO: Put this information into a database
workflows = {}
allocations = {}
partitions = {}

class WorkflowHandler(Resource):
    """Workflow handler.

    Handle the creation, deletion and updating of workflows.
    """

    def post(self, name=None):
        """Create/send over a new workflow.

        Create a new workflow.
        :param name: name of the workflow
        :type name: str
        """
        data = request.get_json()
        if data is not None and 'name' in data:
            name = data['name']
            workflows[name] = data
            url = os.path.join(request.url, name)
            return {
              'url': url,
              'allocation': os.path.join(url, 'allocation'),
            }
        return None

    def get(self, name=None):
        """Get details about a workflow.

        Get a new workflow.
        :param name: name of the workflow
        :type name: str
        """
        # TODO

    def put(self, name=None):
        """Update a workflow.

        Update the workflow.
        :param name: name of the workflow
        :type name: str
        """
        # TODO

    def delete(self, name=None):
        """Delete a workflow.

        Delete a workflow from the system.
        :param name: name of the workflow
        :type name: str
        """
        # TODO


def schedule_best(partition_times):
    """(Naïve implementation)
    Return the best tuple of (partition, time) for this dictionary of
    partitions to current scheduled times.

    :param partition_times: current allocated partitions with a list
                            of allocated times for each partition
    """
    best_time = math.inf
    best_part = None
    for partition in partition_times:
        time = sum(partition_times[partition])
        if time < best_time:
            best_time = time
            best_part = partition
    return best_part, best_time


# TODO: choose_algorithm() and the scheduling algorithms themselves could
#       could be designed to be object-oriented
def fcfs(workflow, partitions):
    """Run a simple FCFS algorithm with the given FCFS."""
    allocation = {
        'status': 'COMPLETE',
        'start_time': 0,
    }
    # Simple FCFS Algorithm
    # TODO: Assumes constant time for each task
    steps_to_partitions = {}
    time = 0
    total_time = 0
    # Create a list of used times for each partition
    partition_times = {pname: [] for pname in partitions}
    # TODO: Set max_runtime per nodes
    for level in workflow['tasks']:
        max_time = 0
        for task in level:
            best_part, best_time = schedule_best(partition_times)
            steps_to_partitions[task['name']] = {
                'partition': best_part,
                'time': best_time,
            }
            partition_times[best_part].append(task['runtime'])
            if task['runtime'] > max_time:
                max_time = task['runtime']
        time += max_time
        total_time += max_time
        # "Level off" the partition_times to match the maximum running times
        for partition in partition_times:
            t = sum(partition_times[partition])
            if t < total_time:
                partition_times[partition].append(total_time - t)
    allocation['steps_to_partition'] = steps_to_partitions
    # TODO
    return allocation

def choose_algorithm():
    """Choose the scheduling algorithm to run."""
    # TODO: Choose the specific scheduling algorithm to run using known
    #       variables
    return fcfs


class AllocationHandler(Resource):
    """Allocation handler - handles main scheduling algorithm."""
    def post(self, name):
        """Start the scheduling algorithm."""
        print(workflows)
        # TODO
        return 'initiating scheduling process'

    def get(self, name):
        """
        Get the allocation that has been calculated or return current status.
        """
        algorithm = choose_algorithm()
        return algorithm(workflows[name], partitions)

class PartitionHandler(Resource):
    """Partition Handler"""
    def post(self, name=None):
        """Create a new partition.

        :param name: name of the parition
        """
        data = request.get_json()
        if data is not None and (name is not None or 'name' in data):
            if name is None:
                name = data['name']
            partitions[name] = data
            # Setup allocation
            allocations[name] = []
            return {'url': os.path.join(request.url, name)}
        # TODO
        return None

    def get(self, name=None):
        """Get a new node."""
        # TODO

    def put(self, name=None):
        """Update a node."""
        # TODO

    def delete(self, name=None):
        """Delete a node."""
        # TODO


class NodeHandler(Resource):
    """Node Handler"""
    def post(self, node_id=None):
        """Create a new node."""
        # TODO

    def get(self, node_id=None):
        """Get information about a node."""
        # TODO

    def put(self, node_id=None):
        """Update a node."""
        # TODO

    def delete(self, node_id=None):
        """Delete a node."""
        # TODO


api.add_resource(WorkflowHandler, '/bee_sched/v1/workflows/',
                 '/bee_sched/v1/workflows/<string:name>')
api.add_resource(AllocationHandler,
                 '/bee_sched/v1/workflows/<string:name>/allocation')
api.add_resource(PartitionHandler, '/bee_sched/v1/partitions/',
                 '/bee_sched/v1/partitions/<string:name>')
api.add_resource(NodeHandler, '/bee_sched/v1/nodes/',
                 '/bee_sched/v1/nodes/<int:node_id>')

if __name__ == '__main__':
    flask_app.run(debug=True, port=5100)
