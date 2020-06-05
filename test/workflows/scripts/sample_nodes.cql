CREATE (:Task {
  task_id: '16fd2706-8baf-433b-82eb-8c7fada847da',
  name: 'some_bogus_task_name',
  command: 'command-name --with --parameters',
  inputs: ['input_file.0', 'input_file.1', 'input_file.2'],
  outputs: ['output_file.0', 'output_file.1'],
  state: 'SUBMITTED'
});

CREATE (:Workflow {
  workflow_id: '6fa459ea-ee8a-3ca4-894e-db77e160355e',
  name: 'a_totally_phony_workflow',
  inputs: ['wf_in.0', 'wf_in.1', 'wf_in.2', 'wf_in.3'],
  outputs: ['wf_out.0', 'wf_out.1'],
  state: 'COMPLETE'
});

CREATE (:Hints:TaskHints {
  // must be array if not a primitive type
  DockerRequirement: ['dockerImageId', '/usr/projects/beedev/toss-tiny-3-5.tar'],
  // this may be better?
  dockerImageId: '/usr/projects/beedev/toss-tiny-3-5.tar'
});

MATCH (n) RETURN n;
