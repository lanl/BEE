import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {createRoot} from 'react-dom/client';
import './bootstrap.min.css';
import {ValidatedForm} from './validation.js';
import {Input, Select} from './util.jsx';

// Data for fields in ClusterConfig
let clusterConfigFields = [
  {
    label: 'Hostname',
    type: 'text',
    name: 'hostname',
    regex: /\w+/,
  },
  {
    label: 'Moniker',
    type: 'text',
    name: 'moniker',
    regex: /\w+/,
  },
  {
    label: 'Workflow Manager Socket Path',
    type: 'text',
    name: 'wfmSocketPath',
    regex: /\w+/,
  },
  {
    label: 'GDB Port',
    type: 'number',
    name: 'gdbPort',
    regex: /\d+/,
  },
];

class ClusterConfig extends ValidatedForm {
  constructor(props) {
    super(props);
    // Calculate starting input values with setInitialValue
    let entries = clusterConfigFields
      .map(field => [field.name, this.props.setInitialValue(field.name)]);
    let currentValues = Object.fromEntries(entries);
    let state = {
      currentValues,
      errors: {},
    };
    if (this.props.edit) {
      Object.assign(state, currentValues);
    }
    this.state = state;
  }

  handleChange(ev, regex, label, name) {
    let currentValues = Object.fromEntries(Object.entries(this.state.currentValues));
    console.log(ev.target.value);
    currentValues[name] = ev.target.value;
    this.setState({currentValues});
    this.handleChangeRegex(ev, regex, label, name);
  }

  render() {
    let handler = (ev) => this.handleInputChange(ev);
    let fieldNames = clusterConfigFields.map(field => field.name);
    let fieldLabels = clusterConfigFields.map(field => field.label);
    let inputs = clusterConfigFields
      .map(field => {
        let error = Object.hasOwn(this.state.errors, field.name) ?
                    this.state.errors[field.name] : null;
        let value = this.state.currentValues[field.name];
        console.log(this.state.currentValues);
        return (
          <Input
            label={field.label}
            type={field.type}
            name={field.name}
            error={error}
            value={value}
            onChange={ev => this.handleChange(ev, field.regex, field.label, field.name)}
          />
        );
      });
    let createCallback = cfg => {
      // Ensure that the hostname doesn't already exist
      if (!this.props.edit
          && this.props.clusters.some(cluster => cluster.hostname == cfg.hostname)) {
        this.setState({errors: {hostname: "This hostname already exists"}});
        return;
      }
      this.setState({errors: {}});
      console.log('createCallback()');
      this.props.handleClusterConfigSubmit(cfg);
      // TODO
    };
    return (
      <>
        <h2>Create Cluster</h2>
        {inputs}
        <div>
          <button
            className="btn btn-primary"
            onClick={() => this.validateAll(fieldNames, fieldLabels, createCallback)}>
            {this.props.edit ? "Edit" : "Create"}
          </button>
        </div>
      </>
    );
  }
}

class Settings extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      view: 'settings',
      cluster: null,
    };
  }

  handleClusterConfigCreate(cfg) {
    window.beeflow.createCluster(cfg)
      .then(_ => {
        // Refresh
        this.props.load();
        this.setState({view: 'settings'});
      })
      .catch(err => {
        this.setState({view: 'error', errorMessage: err});
      });
  }

  handleClusterConfigUpdate(cfg) {
    // TODO
    window.beeflow.updateCluster(cfg)
      .then(_ => {
        // Refresh
        this.props.load();
        this.setState({view: 'settings'});
      })
      .catch(err => {
        this.setState({view: 'error', errorMessage: err});
      });
  }

  // Attempt to connect to the given cluster
  connect(cluster) {
    window.beeflow.connectCluster(cluster)
      .catch(err => {
        alert(err);
        this.setState({view: 'error', errorMessage: err});
      });
  }

  render() {
    let view = null;
    switch (this.state.view) {
    case 'settings':
      // Cluster buttons to click for editing
      let clusters = this.props.clusters
        .map(cluster => {
          let onClick = () => {
            this.setState({
              view: 'cluster-edit',
              cluster,
            });
          };
          return (
            <div className="d-flex justify-content-between m-2">
              <span>{cluster.hostname}</span>
              <div className="btn-group">
                <button className="btn btn-primary" onClick={onClick}>
                  E
                </button>
                <button className="btn btn-primary" onClick={() => this.connect(cluster)}>
                  C
                </button>
              </div>
            </div>
          );
        });
      view = (
        <>
          <h1>Settings</h1>
          <div>
          <h3>Clusters</h3>
          {clusters}
          </div>
          <button
            className="btn btn-primary"
            onClick={() => this.setState({view: 'cluster-config'})}>
            Create cluster
          </button>
        </>
      );
      break;
    case 'cluster-config':
      view = (
        <ClusterConfig
          handleClusterConfigSubmit={(cfg) => this.handleClusterConfigCreate(cfg)}
          setInitialValue={name => ""}
          edit={false}
          clusters={this.props.clusters}
        />
      );
      break;
    case 'cluster-edit':
      view = (
        <ClusterConfig
          handleClusterConfigSubmit={cfg => this.handleClusterConfigUpdate(cfg)}
          edit={true}
          clusters={this.props.clusters}
          setInitialValue={name => this.state.cluster[name]}
        />
      );
      break;
    }

    return (
      <div className="card">
        <div className="card-body">
          {view}
        </div>
      </div>
    );
  }
}

let submitWorkflowFields = [
  {
    label: 'Workflow name',
    type: 'text',
    name: 'wfName',
    regex: /\w+[\d\s\w]*/,
  },
  {
    label: 'Tarball',
    type: 'file',
    name: 'tarball',
    fnameRegex: /[\w\d-_\.]+\.(tar\.(gz|bz2|xz)|tgz)/
  },
  {
    label: 'Main workflow file',
    type: 'text',
    name: 'mainCwl',
    regex: /[\w\d-]+\.cwl/,
  },
  {
    label: 'YAML file',
    type: 'text',
    name: 'yaml',
    regex: /[\w\d-]+\.(yml|yaml)/,
  },
  {
    label: 'Workdir path',
    type: 'text',
    name: 'workdir',
    regex: /[\w\d-\/]+/,
  },
  {
    label: 'Cluster',
    type: 'select',
    name: 'cluster',
    options: [],
  },
];

class SubmitWorkflow extends ValidatedForm {
  constructor(props) {
    super(props);
    // Set the options for clusters
    let clusterField = submitWorkflowFields.find(field => field.name === 'cluster');
    console.log(props.clusters);
    clusterField.options = props.clusters.map(cluster => cluster.hostname);
    this.state = {
      errors: {},
      view: "submit",
      wfID: null,
      errorMessage: null,
    }
  }

  render() {
    let fieldNames = submitWorkflowFields.map(field => field.name);
    let fieldLabels = submitWorkflowFields.map(field => field.label);
    let inputs = submitWorkflowFields
      .map(field => {
        let error = null;
        if (Object.hasOwn(this.state.errors, field.name)) {
          error = this.state.errors[field.name]
        }
        switch (field.type) {
        case 'text':
          return (
            <Input
              type='text'
              name={field.name}
              label={field.label}
              error={error}
              onChange={(ev) => this.handleChangeRegex(ev, field.regex,
                                                       field.label, field.name)}
            />
          );
        case 'file':
          return (
            <Input
              type='file'
              name={field.name}
              label={field.label}
              error={error}
              onChange={(ev) => this.handleChangeFile(ev, field.fnameRegex, field.name)}
            />
          );
        case 'select':
          return (
            <Select
              name={field.name}
              label={field.label}
              options={field.options}
              error={error}
              onChange={(ev) => this.handleChangeSelect(ev, field.label, field.name)}
            />
          );
        default:
          return null;
        }
      });
    let onClick = () => {
      this.validateAll(fieldNames, fieldLabels, data => {
        this.setState({view: "waiting"});
        this.props.handleWorkflowSubmit(data);
      });
    };
    switch (this.state.view) {
    case "submit":
      return (
        <div>
          {inputs}
          <button
            className="btn btn-primary"
            onClick={onClick}>
            Submit workflow
          </button>
        </div>
      );
    case "waiting":
      return (
        <div class="text-center">
          Loading...
          <div class="spinner-border spinner-border-sm" role="status" arria-hidden="true"></div>
        </div>
      );
    case "successful":
      return (
        <div>
          <h2>Submitted workflow</h2>
          Workflow ID: <strong>{this.state.wfID}</strong>
        </div>
      );
    case "error":
      return (
        <div>
          An error occurred during workflow submission:
          {this.state.errorMessage}
        </div>
      );
    }
  }
}

// Show an overview of all workflows
class Workflows extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      view: 'main',
    };
  }

  handleSubmitWorkflowPageClick() {
    this.setState({view: 'create'});
    this.props.setCurrentWorkflow(null);
  }

  render() {
    let body;
    if (this.props.currentWorkflow() !== null) {
      body = (
        <WorkflowDetails
          wfID={this.props.currentWorkflow()}
          handleCancelClick={(wfID) => this.props.handleCancelClick(wfID)}
          handleStopClick={(wfID) => this.props.handleStopClick(wfID)}
          handleStartClick={(wfID => this.props.handleStartClick(wfID))}
        />
      );
    } else if (this.state.view === 'main') {
      let workflowControls = this.props.workflows
        .map(wfl => {
          return (
            <button
              className="btn btn-primary"
              onClick={wfl.handleClick}>
              {wfl.name}
            </button>
          );
        });
      body = (
        <>
          <h1>Workflows</h1>
          {workflowControls}
          <button
            className="btn btn-primary"
            onClick={() => this.handleSubmitWorkflowPageClick()}>
            Submit Workflow
          </button>
        </>
      );
    } else if (this.state.view === 'create') {
      body = (
        <SubmitWorkflow
          clusters={this.props.clusters}
          handleWorkflowSubmit={data => this.props.handleWorkflowSubmit(data)}
          load={this.props.load}
        />
      );
    }
    console.log('rerendering workflow');
    return (
      <div className="card">
        <div className="card-body">
          {body}
        </div>
      </div>
    );
  }
}

// Show details about a particular workflow
function WorkflowDetails(props) {
  return (
    <>
      <p>Workflow ID: {props.wfID}</p>
      <div className="btn-group">
        <button
          className="btn btn-primary"
          onClick={() => props.handleStartClick(props.wfID)}>
          Start
        </button>
        <button
          className="btn btn-primary"
          onClick={() => props.handleCancelClick(props.wfID)}>
          Cancel
        </button>
        <button
          className="btn btn-primary"
          onClick={() => props.handleStopClick(props.wfID)}>
          Stop
        </button>
      </div>
    </>
  );
}

class BEEClient extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      view: 'settings',
      // Current workflow ID
      wfID: null,
      workflows: [],
      clusters: [],
    };
    this.load();
  }

  // Load workflow and cluster info from the backend
  load() {
    // Load the workflows by through the state
    window.beeflow.getWorkflows()
      .then(workflows => {
        // NOTE: Every time `this.setState()` is called, `render()` will be called
        this.setState({workflows});
      });
    window.beeflow.getClusters()
      .then(clusters => {
        console.log('Getting clusters');
        console.log(clusters);
        this.setState({clusters});
      });
  }

  setCurrentWorkflow(wfID) {
    this.setState({wfID});
  }

  // Handle navigation to a particular workflow
  handleWorkflowClick(wfID) {
    console.log(`setting workflow to use ID: ${wfID}`);
    this.setState({view: 'workflow', wfID});
  }

  handleWorkflowSubmit(data) {
    window.beeflow.submitWorkflow(data)
      .then(result => {
        // Refresh the main view
        this.props.load();
        this.handleWorkflowClick(result.wfID);
      })
      .catch(err => {
        this.setState({view: "error", errorMessage: err});
      });
  }

  handleCancelClick(wfID) {
    console.log(`handleCancelClick(${wfID})`);
    window.beeflow.cancelWorkflow(wfID)
      .then(_ => this.load())
      .catch(err => {
        // TODO: Handle the error
      });
  }

  handleStopClick(wfID) {
    console.log(`handleStopClick(${wfID})`);
    // TODO: Is this necessary
  }

  handleStartClick(wfID) {
    window.beeflow.startWorkflow(wfID)
      .then(_ => this.load())
      .catch(err => {
        // TODO: Handle the error.
      });
  }

  handleClusterConfigCreate(data) {
    // TODO: Handle creating a new cluster config
    window.beeflow.createCluster(data)
      .then(_ => this.load())
      .catch(err => {
        // TODO: Handle the error
      });
  }

  render() {
    let workflowButtons = this.state.workflows
      .map(wfl => {
        let className = `btn nav-link ${this.state.wfID == wfl.wfID ? "active" : ""}`;
        return (
          <button
            className={className}
            onClick={() => this.handleWorkflowClick(wfl.wfID)}>
            {wfl.name}
          </button>
        );
      });

    // Build the current view
    let view;
    if (this.state.view === 'settings') {
      view = (
        <Settings
          clusters={this.state.clusters}
          load={() => this.load()}
        />
      );
    } else {
      view = (
        <Workflows
          load={() => this.load()}
          currentWorkflow={() => this.state.wfID}
          setCurrentWorkflow={wfID => this.setCurrentWorkflow(wfID)}
          handleWorkflowSubmit={data => this.handleWorkflowSubmit(data)}
          handleCancelClick={wfID => this.handleCancelClick(wfID)}
          handleStopClick={wfID => this.handleCancelClick(wfID)}
          handleStartClick={wfID => this.handleStartClick(wfID)}
          clusters={this.state.clusters}
          workflows={this.state.workflows}
          wfID={this.state.wfID}
        />
      );
    }

    // This is used to make the nav buttons active when on a certain page
    let navLinkClass = (view) => {
        if (this.state.view == view) {
            return 'btn nav-link active';
        }
        return 'btn nav-link';
    };

    return (
      <div>
        <div className="row">
          <div className="col">
            <nav className="nav flex-column">
              <button
                className={navLinkClass('settings')}
                onClick={() => this.setState({view: 'settings', wfID: null})}>
                Settings
              </button>
              <button
                className={navLinkClass('workflows')}
                onClick={() => this.setState({view: 'workflows', wfID: null})}>
                Workflows
              </button>
            </nav>
          </div>
          <div className="col-6">
            {view}
          </div>
          <div className="col nav flex-column">
            {workflowButtons}
          </div>
        </div>
      </div>
    );
  }
}

const container = document.querySelector('#container');
const root = createRoot(container);
root.render(<BEEClient />);
