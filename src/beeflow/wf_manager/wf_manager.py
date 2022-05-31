from flask import Flask
from flask_restful import Api
from beeflow.wf_manager.resources.jobs_list import JobsList

## Setup the Scheduler
#setup_scheduler()
#log.info(f'wfm_listen_port:{wfm_listen_port}')
#bee_workdir = bc.userconfig.get('DEFAULT','bee_workdir')
#handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='wf_manager.log')
#
## Werkzeug logging
#werk_log = logging.getLogger('werkzeug')
#werk_log.setLevel(logging.INFO)
#werk_log.addHandler(handler)
#
## Flask logging
## Putting this off for another issue so noqa to appease the lama
#flask_app.logger.addHandler(handler) #noqa
#flask_app.run(debug=False, port=str(wfm_listen_port))


#
## Setup each resource
##api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
##api.add_resource(JobActions, '/bee_wfm/v1/jobs/<string:wf_id>')
##api.add_resource(JobUpdate, '/bee_wfm/v1/jobs/update/')
#
#flask_app.run(debug=False)

app = Flask(__name__)
api = Api(app)
api.add_resource(JobsList, '/bee_wfm/v1/jobs/')

if __name__ == "__main__":
    #app, api = create_app()
    app.run()
