const http = require('http');
const FormData = require('form-data');
const axios = require('axios');
const Path = require('path');
const fs = require('fs');
const config = require('./config.js');

const workflow_manager = 'bee_wfm/v1/jobs';

function _url() {
    wfm_listen_port = 9999;
    return `http://127.0.0.1:${wfm_listen_port}/${workflow_manager}/`;
}

function _resource(tag='') {
    return _url() + tag;
}

// Build a request config with some useful defaults
function _build_config(method, url, data = null) {
    let headers = {
        'Authorization': 'Bearer ...',
    };
    if (data !== null) {
        Object.assign(headers, data.getHeaders());
    }
    return {
        method,
        url,
        headers,
        adapter: require('axios/lib/adapters/http'),
        data,
        // Just in case 'no_proxy' is set incorrectly
        proxy: false,
    };
}

function start_workflow(wf_id) {
    axios.post(_resource(wf_id), {

    })
    .then(function (response) {

    })
    .catch(function (error) {
        console.log(error);
        alert("WFM communication failed");
    });
}

async function submit_workflow(workflow) {
	var data = new FormData();
    data.append('workflow_archive', fs.createReadStream(workflow.tarball_path));
    data.append('wf_filename', workflow.tarball_fname);
	data.append('main_cwl', workflow.main_cwl);
    data.append('yaml', workflow.yaml);
    data.append('workdir', workflow.workdir);
	data.append('wf_name', workflow.name);
	
    let config = _build_config('post', _resource(workflow.wf_id), data)
    const results = axios(config)
    .then(function (response) {
        console.log(JSON.stringify(response.data));
        process.stdout.write(JSON.stringify(response.data));
        // Get wf_id
        wf_id = response.data['wf_id']
        // Get task information from response
        tasks = response.data['tasks'];
        return {wf_id, tasks};
    })
    .catch(function (error) {
        console.log("Failed to communicate with WFM");
        console.log(error);
        console.log(error.response.data);
        console.log(error.response.status);
        console.log(error.response.headers);
        // TODO: Is there a log where this data can be saved?
        alert("WFM communication failed");
    });
    return results
}

async function reexecute_workflow(workflow) {
	var data = new FormData();
	data.append('name', workflow.name);
    data.append('workflow_archive', fs.createReadStream(workflow.tarball_path));	

    let config = _build_config('put', _url(), data);
    const results = axios(config)
    .then(function (response) {
        console.log(JSON.stringify(response.data));
        process.stdout.write(JSON.stringify(response.data));
        // Get wf_id
        wf_id = response.data['wf_id']
        // Get task information from response
        tasks = response.data['tasks'];
        return {wf_id, tasks};
    })
    .catch(function (error) {
      //console.log(error);
    });
    return results
}

// Query the current state of a workflow's task.
async function query_workflow(wf_id) {
    let config = _build_config('get', _resource(wf_id));
    const results = axios(config)
    .then(function (response) {
        console.log(JSON.stringify(response.data));
        tasks = response.data['tasks'];
        wf_status = response.data['wf'];
        return {wf_status, tasks};
    })
    .catch(function (error) {
        console.log(error);
    });
    return results;
}

function cancel_workflow(wf_id) {
    axios({
      method: 'delete',
      url: _resource(wf_id),
      proxy: false,
    })
    .then(function (response) {
        console.log(response.data);
    })
    .catch(function (error) {
        console.log(error);
    });
}

// Need to think about making this async
function pause_workflow(wf_id) {
    let config = _build_config('patch', _resource(wf_id), {option: 'pause'});

    const results = axios(config)
    .then(function (response) {
        console.log(JSON.stringify(response.data));
    })
    .catch(function (error) {
        console.log(error);
    });
    return results;
}

// Need to think about making this async
function resume_workflow(wf_id) {
    let config = _build_config('patch', _resource(wf_id), {option: 'resume'});

    const results = axios(config)
    .then(function (response) {
        console.log(JSON.stringify(response.data));
    })
    .catch(function (error) {
        console.log(error);
    });
    return results;
}

async function download_archive(wf_id) {
    const url = _url(wf_id);
    const path = Path.resolve(__dirname, wf_id + '.tgz')
    const writer = fs.createWriteStream(path)
  
    const response = await axios({
      url,
      method: 'patch',
      responseType: 'stream',
      data: {
          'wf_id': wf_id
      },
      proxy: false,
    })
  
    response.data.pipe(writer)
  
    return new Promise((resolve, reject) => {
      writer.on('finish', resolve)
      writer.on('error', reject)
    })
}

module.exports = { submit_workflow, query_workflow, start_workflow, 
                   pause_workflow, resume_workflow, cancel_workflow,
                   reexecute_workflow, download_archive }
