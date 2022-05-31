def get_script_path():
    return os.path.dirname(os.path.realpath(__file__))

def tm_url():
    """Get Task Manager url."""
    task_manager = "bee_tm/v1/task/"
    return f'http://127.0.0.1:{TM_LISTEN_PORT}/{task_manager}'


def sched_url():
    """Get Scheduler url."""
    scheduler = "bee_sched/v1/"
    return f'http://127.0.0.1:{SCHED_LISTEN_PORT}/{scheduler}'


def _resource(component, tag=""):
    """Access Task Manager or Scheduler."""
    if component == "tm":
        url = tm_url() + str(tag)
    elif component == "sched":
        url = sched_url() + str(tag)
    return url

def validate_wf_id(func):
    """Validate tempoary hard coded workflow id."""
    def wrapper(*args, **kwargs):
        wf_id = kwargs['wf_id']
        current_wf_id = wfi.workflow_id
        if wf_id != current_wf_id:
            log.info(f'Wrong workflow id. Set to {wf_id}, but should be {current_wf_id}')
            resp = make_response(jsonify(status='wf_id not found'), 404)
            return resp
        return func(*args, **kwargs)
    return wrapper

def process_running(pid):
    """Check if the process with pid is running"""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def kill_process(pid):
    """Kill the process with pid"""
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        log.info('Process already killed')

