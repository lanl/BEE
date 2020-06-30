#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

from flask import Flask, request
from flask_restful import Resource, Api

import algorithms
import sched_types
import internal


# TODO: Grab this info from the config
SCHEDULER_PORT = 5100

flask_app = Flask(__name__)
api = Api(flask_app)

# Each cluster holds allocation information
clusters = {}
# Each task holds information about the partition/node/cluster it
# it is allocated to
tasks = {}


class ClusterHandler(Resource):
    """Cluster handler.

    Handle creation of clusters.
    """

    def put(self):
        """Create a list of clusters to use for allocation.

        Create new clusters based on a list of clusters with
        detailed information, such as resources and time limits.
        """
        clusters.clear()
        new_clusters = [sched_types.Cluster.decode(c) for c in request.json]
        clusters.update({c.name: c for c in new_clusters})
        return 'created %i cluster(s)' % len(clusters)


class JobScheduleHandler(Resource):
    """Handle scheduling of jobs.

    Schedule jobs with the available resources.
    """

    def post(self):
        """Create a new job/task and schedule it.

        Create a new job/task and run an allocation on the JobHandler.
        """
        task = sched_types.Task.decode(request.json)
        # Schedule the task, update it with the allocation and add it
        # to the list of tasks and the allocation information to the
        # clusters
        internal.schedule(algorithms.fcfs, task, tasks, clusters)
        return task.encode()


class JobUpdateHandler(Resource):
    """Handle updating and deleting of jobs.

    Update jobs, delete jobs, etc.
    """

    def put(self, name):
        """Update a job/task.

        Update a job/task (the status, time running, etc.)
        :param name: name of the task
        :type name: str
        """
        tasks[name] = sched_types.Task.decode(request.json)
        # TODO: Clean up scheduling information in the cluster list
        return 'updated'

    def delete(self, name):
        """Delete a job/task.

        Delete a job/task which may have completed or was stopped.
        :param name: name of the task
        :type name: str
        """
        del tasks[name]
        return 'deleted'


class WorkflowHandler(Resource):
    """Workflow handler to allow for optimization capabilities.

    The workflow handler allows for the scheduling of entire workflows,
    based on their individual tasks in order to allow for scheduling
    optimizations.
    """
    # TODO


api.add_resource(ClusterHandler, '/bee_sched/v1/clusters')
api.add_resource(JobScheduleHandler, '/bee_sched/v1/jobs')
api.add_resource(JobUpdateHandler, '/bee_sched/v1/jobs/<string:name>')
api.add_resource(WorkflowHandler, '/bee_sched/v1/workflows')
# api.add_resource(ScheduleHandler, '/bee_sched/v1/schedule')

if __name__ == '__main__':
    flask_app.run(debug=True, port=SCHEDULER_PORT)
