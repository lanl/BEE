import os
import jsonpickle
from flask import make_response, jsonify
from flask_restful import Resource, Api, reqparse
from werkzeug.datastructures import FileStorage

# Client registers with the workflow manager.
# Workflow manager returns a workflow ID used for subsequent communication

def get_beeworkdir():   
    return 'beeworkdir'

class JobsList(Resource):
    """Class def to interact with workflow job listing."""

    def __init__(self):
        """Initialize job list class."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('wf_name', type=str, required=False,
                                   location='json')
        self.reqparse.add_argument('wf_filename', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('workflow', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('yaml', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('main_cwl', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('workflow_archive', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('wf_id', type=FileStorage, required=False,
                                   location='files')
        super(JobsList, self).__init__()

    def get(self):
        """Return list of workflows to client"""
        # For each dir in bee_workdir look at its state at .bee_state
        bee_workdir = get_beeworkdir()
        workflows_dir = os.path.join(bee_workdir, 'workflows')
        job_list = []
        if os.path.isdir(workflows_dir):
            workflows = next(os.walk(workflows_dir))[1]
            for wf_id in workflows:
                wf_path = os.path.join(workflows_dir, wf_id) 
                status_path = os.path.join(wf_path, 'bee_wf_status')
                name_path = os.path.join(wf_path, 'bee_wf_name')
                status = pathlib.Path(status_path).read_text()
                name = pathlib.Path(name_path).read_text()
                job_list.append([name, wf_id, status])
        resp = make_response(jsonify(job_list=jsonpickle.encode(job_list)), 200)
        return resp

    def post(self):
        global wfi
        global wf_profiler
        """Get a workflow or give file not found error."""
        data = self.reqparse.parse_args()

        if data['workflow'] == "":
            resp = make_response(jsonify(msg='No file found', status='error'), 400)
            return resp
        # Workflow file
        print(data)
        wf_tarball = data['workflow']
        print(wf_tarball)
        wf_filename = data['wf_filename'].read().decode()
        main_cwl = data['main_cwl'].read().decode()
        job_name = data['wf_name'].read().decode()
        # None if not sent
        yaml_file = data['yaml']

        if wf_tarball:
            # We have to bind mount a new GDB with charliecloud.
            kill_gdb()
            # Remove the old gdb
            remove_gdb()
            # Start a new GDB 
            bee_workdir = get_beeworkdir()
            gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
            script_path = get_script_path()
            gdb_proc = StartGDB(bc, gdb_workdir)
            # Need to wait a moment for the GDB
            log.info('waiting {}s for GDB to come up'.format(gdb_sleep_time))
            time.sleep(gdb_sleep_time)

            if wfi:
                if wfi.workflow_initialized() and wfi.workflow_loaded():
                    # Clear the workflow if we've already run one
                    wfi.finalize_workflow()

            # Save the workflow temporarily to this folder for the parser
            #
            temp_dir = tempfile.mkdtemp()
            temp_tarball_path = os.path.join(temp_dir, wf_filename)
            wf_tarball.save(temp_tarball_path)
            # Archive tarballs must be tgz 
            extension = '.tgz'
            wf_dirname = wf_filename[:len(extension)]
            subprocess.run(['tar', 'xf', f'{wf_filename}', '--strip-components', '1'], cwd=temp_dir)

            parser = CwlParser()
            temp_cwl_path = os.path.join(temp_dir, main_cwl)
            if yaml_file != None:
                yaml_file = yaml_file.read().decode()
                temp_yaml_path = os.path.join(temp_dir, yaml_file)
                wfi = parser.parse_workflow(temp_cwl_path, temp_yaml_path)
            else:
                wfi = parser.parse_workflow(temp_cwl_path)

            # Initialize the workflow profiling code
            fname = '{}.json'.format(job_name)
            bee_workdir = get_beeworkdir()
            profile_dir = os.path.join(bee_workdir, 'profiles')
            os.makedirs(profile_dir, exist_ok=True)
            output_path = os.path.join(profile_dir, fname)
            wf_profiler = WorkflowProfiler(job_name, output_path)

            # Save the workflow to the workflow_id dir
            wf_id = wfi.workflow_id
            bee_workdir = get_beeworkdir()
            workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
            os.makedirs(workflow_dir)
            #workflow_path = os.path.join(workflow_dir, wf_filename)
            #wf_tarball.save(workflow_path)

            # Copy workflow files to archive
            for f in os.listdir(temp_dir):
                f_path = os.path.join(temp_dir, f)
                if os.path.isfile(f_path):
                    shutil.copy(f_path, workflow_dir)

            # Create status file
            status_path = os.path.join(workflow_dir, 'bee_wf_status')
            with open(status_path, 'w') as status:
                status.write('Pending')

            # Create wf name file 
            name_path = os.path.join(workflow_dir, 'bee_wf_name')
            with open(name_path, 'w') as name:
                name.write(job_name)
            resp = make_response(jsonify(msg='Workflow uploaded', status='ok', wf_id=wf_id), 201)
            return resp
        else:
            resp = make_response(jsonify(msg='File corrupted', status='error'), 400)
            return resp


    def put(self):
        """ReExecute a workflow"""
        global reeexecute
        data = self.reqparse.parse_args()
        if data['workflow_archive'] == "":
            resp = make_response(jsonify(msg='No file found', status='error'), 400)
            return resp

        workflow_archive = data['workflow_archive']
        filename = data['wf_filename'].read().decode()
        job_name = data['wf_name'].read().decode()

        if workflow_archive:
            # Make a temp directory to store the archive
            tmp_path = tempfile.mkdtemp()
            archive_path = os.path.join(tmp_path, filename)
            workflow_archive.save(archive_path)
            # Extract to tmp directory
            subprocess.run(['tar', '-xf', archive_path, '-C', tmp_path])

            # Kill existing GDB if needed
            kill_gdb()
            remove_gdb()

            # Copy GDB to gdb_workdir
            archive_dir = filename.split('.')[0]
            gdb_path = os.path.join(tmp_path, archive_dir, 'gdb')
            bee_workdir = get_beeworkdir()
            gdb_workdir = os.path.join(bee_workdir, 'current_gdb')

            shutil.copytree(gdb_path, gdb_workdir) 

             # Launch new container with bindmounted GDB
            script_path = get_script_path()
            gdb_proc = StartGDB(bc, gdb_workdir, reexecute=True)
            log.info('waiting {}s for GDB to come up'.format(gdb_sleep_time))
            time.sleep(gdb_sleep_time)

            # Initialize the database connection object
            wfi.initialize_workflow(inputs=None, outputs=None, existing=True)
            # Reset the workflow state and generate a new workflow ID
            wfi.reset_workflow()
            wf_id = wfi.workflow_id
            reexecute = True

            # Save the workflow to the workflow_id dir
            wf_id = wfi.workflow_id
            workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
            os.makedirs(workflow_dir)

            # Create status file
            status_path = os.path.join(workflow_dir, 'bee_wf_status')
            with open(status_path, 'w') as status:
                status.write('Pending')

            # Create wf name file 
            name_path = os.path.join(workflow_dir, 'bee_wf_name')
            with open(name_path, 'w') as name:
                name.write(job_name)

            # Return the wf_id and created
            resp = make_response(jsonify(wf_id=wf_id), 201)
            return resp

    def patch(self):
        """Copy workflow archive"""
        data = self.reqparse.parse_args()
        wf_id = data['wf_id'].read().decode()
        bee_workdir = get_beeworkdir()
        archive_path = os.path.join(bee_workdir, 'archives', wf_id + '.tgz')
        with open(archive_path, 'rb') as a:
           archive_file = jsonpickle.encode(a.read())
        archive_filename = os.path.basename(archive_path)
        resp = make_response(jsonify(archive_file=archive_file, 
            archive_filename=archive_filename), 200)
        return resp

