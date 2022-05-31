if bc.userconfig.has_section('workflow_manager'):
    # Try getting listen port from config if exists, use WM_PORT if it doesnt exist
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port', bc.default_wfm_port)
    log.info(f"wfm_listen_port {wfm_listen_port}")
else:
    log.info("[workflow_manager] section not found in configuration file, default values\
 will be added")

    wfm_dict = {
        'listen_port': bc.default_wfm_port,
    }

    bc.modify_section('user', 'workflow_manager', wfm_dict)
    sys.exit("Please check " + str(bc.userconfig_file) + " and restart WorkflowManager")

if bc.userconfig.has_section('task_manager'):
    # Try getting listen port from config if exists, use default if it doesnt exist
    TM_LISTEN_PORT = bc.userconfig['task_manager'].get('listen_port', bc.default_tm_port)
else:
    log.info("[task_manager] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    TM_LISTEN_PORT = bc.default_tm_port

if bc.userconfig.has_section('scheduler'):
    # Try getting listen port from config if exists, use 5050 if it doesnt exist
    SCHED_LISTEN_PORT = bc.userconfig['scheduler'].get('listen_port', bc.default_sched_port)
else:
    log.info("[scheduler] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    SCHED_LISTEN_PORT = bc.default_sched_port

bee_workdir = bc.userconfig.get('DEFAULT','bee_workdir')
UPLOAD_FOLDER = os.path.join(bee_workdir, 'current_workflow')
# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# gdb sleep time
gdb_sleep_time = bc.userconfig['graphdb'].getint('sleep_time', 10)

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

