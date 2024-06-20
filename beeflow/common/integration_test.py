"""BEE integration tests."""
import glob
from pathlib import Path
import os
import shutil
import sys
import uuid
import typer

from beeflow.common.integration import utils
from beeflow.common.integration import generated_workflows
from beeflow.common.config_driver import BeeConfig as bc


TEST_RUNNER = utils.TestRunner()


@TEST_RUNNER.add()
def copy_container(outer_workdir):
    """Prepare, check results of using `beeflow:copyContainer` then do cleanup."""
    # `beeflow:copyContainer` workflow
    container_path = f'/tmp/copy_container-{uuid.uuid4().hex}.tar.gz'
    container_name = 'copy-container'
    workdir = utils.make_workflow_workdir(outer_workdir)
    container = utils.Container(container_name, generated_workflows.DOCKER_FILE_PATH,
                                container_path)
    workflow_path = os.path.join(outer_workdir, f'bee-cc-workflow-{uuid.uuid4().hex}')
    main_input = 'copy_container'
    docker_requirement = {
        'beeflow:copyContainer': container_path,
    }
    main_cwl, job_file = generated_workflows.builder_workflow(workflow_path, docker_requirement,
                                                              main_input)
    workflow = utils.Workflow('copy-container', workflow_path, main_cwl=main_cwl,
                              job_file=job_file, workdir=workdir,
                              containers=[container])
    yield [workflow]
    utils.check_completed(workflow)
    # Ensure the output file was created
    path = os.path.join(workdir, main_input)
    utils.check_path_exists(path)
    os.remove(path)
    # Ensure that the container has been copied into the archive
    container_archive = bc.get('builder', 'container_archive')
    basename = os.path.basename(container_path)
    path = os.path.join(container_archive, basename)
    utils.check_path_exists(path)
    os.remove(path)
    utils.ch_image_delete(container_name)


@TEST_RUNNER.add()
def use_container(outer_workdir):
    """Prepare, check results of using `beeflow:useContainer` and clean up."""
    # `beeflow:useContainer` workflow
    container_path = os.path.join(outer_workdir, f'use_container-{uuid.uuid4().hex}.tar.gz')
    container_name = 'use-container'
    container_workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(container_workdir)
    container = utils.Container(container_name, generated_workflows.DOCKER_FILE_PATH,
                                container_path)
    workflow_path = os.path.join(outer_workdir, f'bee-use-ctr-workflow-{uuid.uuid4().hex}')
    main_input = 'use_ctr'
    docker_requirement = {
        'beeflow:useContainer': container_path,
    }
    main_cwl, job_file = generated_workflows.builder_workflow(
        workflow_path,
        docker_requirement,
        main_input,
    )
    workflow = utils.Workflow('use-container', workflow_path, main_cwl=main_cwl,
                              job_file=job_file, workdir=container_workdir,
                              containers=[container])
    yield [workflow]
    utils.check_completed(workflow)
    path = os.path.join(container_workdir, main_input)
    utils.check_path_exists(path)
    # This container should not have been copied into the container archive
    container_archive = bc.get('builder', 'container_archive')
    basename = os.path.basename(container_path)
    path = Path(container_archive, basename)
    utils.ci_assert(
        not path.exists(),
        f'the container "{basename}" was copied into the container archive'
    )
    utils.ch_image_delete(container_name)


@TEST_RUNNER.add()
def docker_file(outer_workdir):
    """Ensure that the `dockerFile` example ran properly and then clean up."""
    # `dockerFile` workflow
    workflow_path = os.path.join(outer_workdir, f'bee-df-workflow-{uuid.uuid4().hex}')
    # Copy the Dockerfile to the workdir path
    os.makedirs(workflow_path)
    workdir = utils.make_workflow_workdir(outer_workdir)
    shutil.copy(generated_workflows.DOCKER_FILE_PATH, os.path.join(workflow_path, 'Dockerfile'))
    container_name = 'docker_file_test'
    docker_requirement = {
        'dockerFile': 'Dockerfile',
        'beeflow:containerName': container_name,
    }
    main_input = 'docker_file'
    main_cwl, job_file = generated_workflows.builder_workflow(
        workflow_path,
        docker_requirement,
        main_input,
    )
    workflow = utils.Workflow('docker-file', workflow_path, main_cwl=main_cwl,
                              job_file=job_file, workdir=workdir, containers=[])
    yield [workflow]
    utils.check_completed(workflow)
    path = os.path.join(workdir, main_input)
    utils.check_path_exists(path)
    # The container should have been copied into the archive
    container_archive = bc.get('builder', 'container_archive')
    tarball = f'{container_name}.tar.gz'
    path = os.path.join(container_archive, tarball)
    utils.check_path_exists(path)
    os.remove(path)
    # Check that the container is listed
    images = utils.ch_image_list()
    utils.ci_assert(container_name in images,
                    f'cannot find expected container "{container_name}"')
    utils.ch_image_delete(container_name)


@TEST_RUNNER.add()
def docker_pull(outer_workdir):
    """Prepare, then check that the `dockerPull` option was successful."""
    # `dockerPull` workflow
    workflow_path = os.path.join(outer_workdir, f'bee-dp-workflow-{uuid.uuid4().hex}')
    workdir = utils.make_workflow_workdir(outer_workdir)
    container_name = generated_workflows.BASE_CONTAINER
    docker_requirement = {
        'dockerPull': container_name,
    }
    main_input = 'docker_pull'
    main_cwl, job_file = generated_workflows.builder_workflow(
        workflow_path,
        docker_requirement,
        main_input,
    )
    workflow = utils.Workflow('docker-pull', workflow_path, main_cwl=main_cwl,
                              job_file=job_file, workdir=workdir, containers=[])
    yield [workflow]
    utils.check_completed(workflow)
    path = os.path.join(workdir, main_input)
    utils.check_path_exists(path)
    # Check that the image tarball is in the archive
    container_archive = bc.get('builder', 'container_archive')
    path = os.path.join(container_archive, f'{container_name}.tar.gz')
    utils.check_path_exists(path)
    os.remove(path)
    # Commenting the below out for now; looks like Charliecloud 0.32 isn't
    # showing base containers for some reason?
    # Check for the image with `ch-image list`
    # images = utils.ch_image_list()
    # utils.ci_assert(container_name in images,
    #                 f'could not find expected container "{container_name}"')
    # utils.ch_image_delete(container_name)


@TEST_RUNNER.add()
def multiple_workflows(outer_workdir):
    """Test running three different workflows at the same time."""
    output_file = 'output_file'
    workflow_data = []
    workflows = []
    for i in range(3):
        workdir = utils.make_workflow_workdir(outer_workdir)
        workflow_path = Path(outer_workdir, uuid.uuid4().hex)
        main_cwl, job_file = generated_workflows.simple_workflow(workflow_path, output_file)
        workflow = utils.Workflow(f'multi-workflow-{i}', workflow_path,
                                  main_cwl=main_cwl, job_file=job_file,
                                  workdir=workdir, containers=[])
        workflow_data.append({
            'workdir': workdir,
            'workflow_path': workflow_path,
        })
        workflows.append(workflow)
    yield workflows
    for workflow in workflows:
        utils.check_completed(workflow)
    for wfl_info in workflow_data:
        workdir = wfl_info['workdir']
        workflow_path = wfl_info['workflow_path']
        # Each test should have touched this file
        path = Path(workdir, output_file)
        utils.check_path_exists(path)


@TEST_RUNNER.add()
def build_failure(outer_workdir):
    """Test running a workflow with a bad container."""
    workdir = utils.make_workflow_workdir(outer_workdir)
    workflow = utils.Workflow('build-failure', 'ci/test_workflows/build-failure',
                              main_cwl='workflow.cwl', job_file='input.yml',
                              workdir=workdir, containers=[])
    yield [workflow]
    utils.check_workflow_failed(workflow)
    # Only one task
    task_state = workflow.task_states[0][2]
    utils.ci_assert(task_state == 'BUILD_FAIL',
                    f'task was not in state BUILD_FAIL as expected: {task_state}')


@TEST_RUNNER.add()
def dependent_tasks_fail(outer_workdir):
    """Test that dependent tasks don't run after a failure."""
    workdir = utils.make_workflow_workdir(outer_workdir)
    workflow = utils.Workflow('failure-dependent-tasks',
                              'ci/test_workflows/failure-dependent-tasks',
                              main_cwl='workflow.cwl', job_file='input.yml',
                              workdir=workdir, containers=[])
    yield [workflow]
    utils.check_workflow_failed(workflow)
    # Check each task state
    fail_state = workflow.get_task_state_by_name('fail')
    utils.ci_assert(fail_state == 'FAILED',
                    f'task fail did not fail as expected: {fail_state}')
    for task in ['dependent0', 'dependent1', 'dependent2']:
        task_state = workflow.get_task_state_by_name(task)
        utils.ci_assert(task_state == 'DEP_FAIL',
                        f'task {task} did not get state DEP_FAIL as expected: {task_state}')


@TEST_RUNNER.add()
def pre_post_script(outer_workdir):
    """Test that the beeflow:ScriptRequirement works."""
    workdir = utils.make_workflow_workdir(outer_workdir)
    workflow = utils.Workflow('pre-post-script', 'ci/test_workflows/pre-post-script',
                              main_cwl='workflow.cwl', job_file='input.yml',
                              workdir=workdir, containers=[])
    yield [workflow]
    utils.check_completed(workflow)
    # Ensure files were touched by the pre and post scripts
    utils.check_path_exists(Path(workdir, 'pre.txt'))
    utils.check_path_exists(Path(workdir, 'post.txt'))


@TEST_RUNNER.add(ignore=True)
def checkpoint_restart(outer_workdir):
    """Test the clamr-ffmpeg checkpoint restart workflow."""
    workdir = utils.make_workflow_workdir(outer_workdir)
    workflow = utils.Workflow('checkpoint-restart',
                              'ci/test_workflows/clamr-wf-checkpoint',
                              main_cwl='clamr_wf.cwl', job_file='clamr_job.yml',
                              workdir=workdir, containers=[])
    yield [workflow]
    utils.check_completed(workflow)
    # Check for the movie file
    path = Path(workdir, 'CLAMR_movie.mp4')
    utils.check_path_exists(path)


@TEST_RUNNER.add(ignore=True)
def checkpoint_restart_failure(outer_workdir):
    """Test a checkpoint restart workflow that continues past 'num_retries'."""
    workdir = utils.make_workflow_workdir(outer_workdir)
    workflow = utils.Workflow('checkpoint-too-long',
                              'ci/test_workflows/checkpoint-too-long',
                              main_cwl='workflow.cwl', job_file='input.yml',
                              workdir=workdir, containers=[])
    yield [workflow]
    utils.check_workflow_failed(workflow)


@TEST_RUNNER.add(ignore=True)
def comd_mpi(outer_workdir):
    """Test the comd-mpi workflow."""
    workdir = utils.make_workflow_workdir(outer_workdir)
    workflow = utils.Workflow('comd-mpi', 'ci/test_workflows/comd-mpi',
                              main_cwl='comd_wf.cwl', job_file='comd_job.yml',
                              workdir=workdir, containers=[])
    yield [workflow]
    utils.check_completed(workflow)
    fnames = glob.glob('CoMD-mpi.*.yaml', root_dir=workdir)
    utils.ci_assert(len(fnames) > 0, 'missing comd output yaml file')


def test_input_callback(arg):
    """Parse a list of tests separated by commas."""
    return arg.split(',') if arg is not None else None


def main(tests = typer.Option(None, '--tests', '-t',  # noqa (conflict on '=' sign)
                              callback=test_input_callback,
                              help='tests run as comma-separated string'),
         show_tests: bool = typer.Option(False, '--show-tests', '-s',  # noqa (conflict on '=' sign)
                                         help='show a list of all tests'),
         timeout: int = typer.Option(utils.TIMEOUT, '--timeout',
                                     help='workflow timeout in seconds')):
    """Launch the integration tests."""
    if show_tests:
        print('INTEGRATION TEST CASES:')
        for test_name, ignore in TEST_RUNNER.test_details():
            print('*', test_name, '(ignored)' if ignore else '')
        return
    generated_workflows.init()
    TEST_RUNNER.timeout = timeout
    # Run the workflows and then show completion results
    ret = TEST_RUNNER.run(tests)
    # ret = test_workflows(WORKFLOWS)
    # General clean up
    os.remove(generated_workflows.DOCKER_FILE_PATH)
    sys.exit(ret)
# Ignore W0231: This is a user-defined exception and I don't think we need to call
#               __init__ on the base class.
# pylama:ignore=W0231
