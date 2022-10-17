const http = require('http');
const FormData = require('form-data');
const axios = require('axios');
const Path = require('path');
const fs = require('fs');
const config = require('./config.js');

workflow_manager = 'bee_wfm/v1/jobs'

function _url() {
    wfm_listen_port = 9999
    return `http://127.0.0.1:${wfm_listen_port}/${workflow_manager}/`
}

function _resource(tag='') {
    return _url() + tag
}

function start_workflow(wf_id) {
    axios.post(_resource(wf_id), {

    })
    .then(function (response) {

    })
    .catch(function (error) {

    });

}

async function submit_workflow(workflow) {
	var data = new FormData();
    data.append('tarball', fs.createReadStream(workflow.tarball_path));	
	data.append('main_cwl', workflow.main_cwl);
    data.append('yaml', workflow.yaml);
	data.append('name', workflow.name);
	
    var config = {
      method: 'post',
      //url: 'http://127.0.0.1:9999/bee_wfm/v1/jobs/',
      url: _resource(workflow.wf_id),
      headers: { 
        'Authorization': 'Bearer ...', 
        ...data.getHeaders()
      },
	  adapter: require('axios/lib/adapters/http'),
      data : data
    };
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

async function reexecute_workflow(workflow) {
	var data = new FormData();
	data.append('name', workflow.name);
    data.append('workflow_archive', fs.createReadStream(workflow.tarball_path));	
	
    var config = {
      method: 'put',
      //url: 'http://127.0.0.1:9999/bee_wfm/v1/jobs/',
      url: _url(),
      headers: { 
        'Authorization': 'Bearer ...', 
        ...data.getHeaders()
      },
	  adapter: require('axios/lib/adapters/http'),
      data : data
    };
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

    var config = {
      method: 'get',
      //url: 'http://127.0.0.1:9999/bee_wfm/v1/jobs/',
      url: _resource(wf_id),
      headers: { 
        'Authorization': 'Bearer ...', 
      },
	  adapter: require('axios/lib/adapters/http'),
      params : { wf_id: wf_id }
    };

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
    axios.delete(_resource(wf_id), {
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
    var config = {
      method: 'patch',
      url: _resource(wf_id),
      headers: { 
        'Authorization': 'Bearer ...', 
      },
	  adapter: require('axios/lib/adapters/http'),
      data : {  'option': 'pause' }
    };

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
    var config = {
      method: 'patch',
      url: _resource(wf_id),
      headers: { 
        'Authorization': 'Bearer ...', 
      },
	  adapter: require('axios/lib/adapters/http'),
      data: { 'option': 'resume' }
    };

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
      method: 'PATCH',
      responseType: 'stream',
      data: {
          'wf_id': wf_id
      }
    })
  
    response.data.pipe(writer)
  
    return new Promise((resolve, reject) => {
      writer.on('finish', resolve)
      writer.on('error', reject)
    })
}
// function resume_workflow(archive_path, wf_name) {
// 
// }

//function list_workflows() {
//    axios.get(_url())
//    .then(function (response) {
//        console.log(response.data);
//    })
//    .catch(function (error) {
//        console.log(error);
//    });
//}
//download_archive('dde31d54-af90-4097-8aac-95d3ab7c6ac0');
//resume_workflow('1962b973-4292-4c39-98a1-c59fd7de9a5b');
module.exports = { submit_workflow, query_workflow, start_workflow, 
                   pause_workflow, resume_workflow, cancel_workflow,
                   reexecute_workflow, download_archive }
