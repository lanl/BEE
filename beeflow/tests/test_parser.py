#! /usr/bin/env python3
"""Unit test module for the BEE CWL parser module."""

from pathlib import Path
import unittest
from beeflow.common.parser import CwlParser, CwlParseError
from beeflow.common.wf_data import (generate_workflow_id, Workflow, Task, Hint,
                                    StepInput, StepOutput, InputParameter, OutputParameter)


REPO_PATH = Path(*Path(__file__).parts[:-3])


def find(path):
    """Find a path relative to the root of the repo."""
    return str(Path(REPO_PATH, path))


class TestParser(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Initialize the CWL parser."""
        cls.parser = CwlParser()

    def test_parse_workflow_yaml(self):
        """Test parsing of workflow with a YAML input job file."""
        cwl_wf_file = find("examples/clamr-ffmpeg-build/clamr_wf.cwl")
        cwl_job_yaml = find("examples/clamr-ffmpeg-build/clamr_job.yml")
        workflow_id = generate_workflow_id()
        workflow, tasks = self.parser.parse_workflow(workflow_id, cwl_wf_file, cwl_job_yaml)

        self.assertEqual(workflow, WORKFLOW_GOLD)
        self.assertListEqual(tasks, TASKS_GOLD)
        for task in tasks:
            self.assertEqual(task.workflow_id, workflow_id)

    def test_parse_workflow_script(self):
        """Test parsing of workflow with a YAML input job file."""
        cwl_wf_file = find("beeflow/data/cwl/bee_workflows/clamr-ffmpeg-build_script/clamr_wf.cwl") #noqa
        cwl_job_yaml = find("beeflow/data/cwl/bee_workflows/clamr-ffmpeg-build_script/clamr_job.yml") #noqa

        workflow_id = generate_workflow_id()

        workflow, tasks = self.parser.parse_workflow(workflow_id, cwl_wf_file, cwl_job_yaml)

        self.assertEqual(workflow, WORKFLOW_GOLD)
        self.assertListEqual(tasks, TASKS_GOLD_SCRIPT)
        for task in tasks:
            self.assertEqual(task.workflow_id, workflow_id)

    def test_parse_workflow_validate_script(self):
        """Test parsing of workflow and validate pre/post script files."""
        cwl_wf_file = find("beeflow/data/cwl/bee_workflows/clamr-ffmpeg-validate_script/clamr_wf.cwl") #noqa
        cwl_job_yaml = find("beeflow/data/cwl/bee_workflows/clamr-ffmpeg-validate_script/clamr_job.yml") #noqa

        workflow_id = generate_workflow_id()

        with self.assertRaises(Exception) as context:
            self.parser.parse_workflow(workflow_id, cwl_wf_file, cwl_job_yaml)

        self.assertEqual(context.exception.args[0], "No shebang line found in pre_run.sh")

    def test_parse_workflow_validate_shell(self):
        """Test parsing of workflow and check shell option matches pre/post script shebang line."""
        cwl_wf_file = find("ci/test_workflows/shell_validate/workflow.cwl") #noqa
        cwl_job_yaml = find("ci/test_workflows/shell_validate/input.yml") #noqa

        workflow_id = generate_workflow_id()

        with self.assertRaises(Exception) as context:
            self.parser.parse_workflow(workflow_id, cwl_wf_file, cwl_job_yaml)

        self.assertEqual(context.exception.args[0], "CWL file shell #!/bin/bash does not match post.sh shell #!/bin/bashoo") #noqa

    def test_parse_workflow_json(self):
        """Test parsing of workflow with a JSON input job file."""
        cwl_wf_file = find("examples/clamr-ffmpeg-build/clamr_wf.cwl")
        cwl_job_json = find("examples/clamr-ffmpeg-build/clamr_job.json")
        workflow_id = generate_workflow_id()

        workflow, tasks = self.parser.parse_workflow(workflow_id, cwl_wf_file, cwl_job_json)

        self.assertEqual(workflow, WORKFLOW_GOLD)
        self.assertListEqual(tasks, TASKS_GOLD)
        for task in tasks:
            self.assertEqual(task.workflow_id, workflow_id)

    def test_parse_workflow_no_job(self):
        """Test parsing of a workflow without an input job file."""
        cwl_wf_file = find("beeflow/tests/cf.cwl")
        workflow_id = generate_workflow_id()
        # cwl_wf_file = "examples/clamr-ffmpeg-build/clamr_wf.cwl"

        workflow, tasks = self.parser.parse_workflow(workflow_id, cwl_wf_file)

        self.assertEqual(workflow, WORKFLOW_NOJOB_GOLD)
        self.assertListEqual(tasks, TASKS_NOJOB_GOLD)
        for task in tasks:
            self.assertEqual(task.workflow_id, workflow_id)

    def test_parse_workflow_missing_input(self):
        """Test parsing a workflow with a missing input value in the input file."""
        cwl_wf_file = find('ci/test_workflows/missing-input/workflow.cwl')
        cwl_job_yaml = find('ci/test_workflows/missing-input/input.yml')

        workflow_id = generate_workflow_id()

        with self.assertRaises(CwlParseError):
            _, _ = self.parser.parse_workflow(workflow_id, cwl_wf_file, cwl_job_yaml)


WORKFLOW_GOLD_SCRIPT = Workflow(
    name='clamr_wf',
    hints=[],
    requirements=[],
    inputs={InputParameter(id='input_format', type='string', value='image2'),
            InputParameter(id='time_steps', type='int', value=5000),
            InputParameter(id='output_filename', type='string', value='./CLAMR_movie.mp4'),
            InputParameter(id='frame_size', type='string', value='800x800'),
            InputParameter(id='frame_rate', type='int', value=12),
            InputParameter(id='max_levels', type='int', value=3),
            InputParameter(id='graphics_type', type='string', value='png'),
            InputParameter(id='steps_between_outputs', type='int', value=10),
            InputParameter(id='pixel_format', type='string', value='yuv420p'),
            InputParameter(id='grid_resolution', type='int', value=32),
            InputParameter(id='steps_between_graphics', type='int', value=25)},
    outputs={OutputParameter(id='clamr_stdout', type='File', value=None,
                             source='clamr/clamr_stdout'),
             OutputParameter(id='clamr_movie', type='File', value=None, source='ffmpeg/movie'),
             OutputParameter(id='ffmpeg_stderr', type='File', value=None,
                             source='ffmpeg/ffmpeg_stderr'),
             OutputParameter(id='clamr_time_log', type='File', value=None,
                             source='clamr/time_log')},
    workflow_id=generate_workflow_id())


WORKFLOW_GOLD = Workflow(
    name='clamr_wf',
    hints=[],
    requirements=[],
    inputs={InputParameter(id='input_format', type='string', value='image2'),
            InputParameter(id='time_steps', type='int', value=5000),
            InputParameter(id='output_filename', type='string', value='CLAMR_movie.mp4'),
            InputParameter(id='frame_size', type='string', value='800x800'),
            InputParameter(id='frame_rate', type='int', value=12),
            InputParameter(id='max_levels', type='int', value=3),
            InputParameter(id='graphics_type', type='string', value='png'),
            InputParameter(id='steps_between_outputs', type='int', value=10),
            InputParameter(id='pixel_format', type='string', value='yuv420p'),
            InputParameter(id='grid_resolution', type='int', value=32),
            InputParameter(id='steps_between_graphics', type='int', value=25)},
    outputs={OutputParameter(id='clamr_stdout', type='File', value=None,
                             source='clamr/clamr_stdout'),
             OutputParameter(id='clamr_movie', type='File', value=None, source='ffmpeg/movie'),
             OutputParameter(id='ffmpeg_stderr', type='File', value=None,
                             source='ffmpeg/ffmpeg_stderr'),
             OutputParameter(id='clamr_time_log', type='File', value=None,
                             source='clamr/time_log')},
    workflow_id=generate_workflow_id())

TASKS_GOLD_SCRIPT = [
    Task(
        name='clamr',
        base_command='/CLAMR/clamr_cpuonly',
        hints=[Hint(class_='DockerRequirement', params={'dockerFile': '# Dockerfile.clamr-ffmpeg\n# Developed on Chicoma @lanl\n# Patricia Grubel <pagrubel@lanl.gov>\n\nFROM debian:11\n\n\nRUN apt-get update && \\\n    apt-get install -y wget gnupg git cmake ffmpeg g++ make openmpi-bin libopenmpi-dev libpng-dev libpng16-16 libpng-tools imagemagick libmagickwand-6.q16-6 libmagickwand-6.q16-dev\n\nRUN git clone https://github.com/lanl/CLAMR.git\nRUN cd CLAMR && cmake . && make clamr_cpuonly\n', 'beeflow:containerName': 'clamr-ffmpeg'}), #noqa
               Hint(class_='beeflow:ScriptRequirement', params={'enabled': True, 'pre_script': 'echo "Before run"', 'post_script': 'echo "After run"', 'shell': '/bin/bash'})], #noqa
        requirements=[],
        inputs=[StepInput(id='graphic_steps', type='int', value=None, default=None,
                          source='steps_between_graphics', prefix='-g', position=None,
                          value_from=None),
                StepInput(id='graphics_type', type='string', value=None, default=None,
                          source='graphics_type', prefix='-G', position=None, value_from=None),
                StepInput(id='grid_res', type='int', value=None, default=None,
                          source='grid_resolution', prefix='-n', position=None, value_from=None),
                StepInput(id='max_levels', type='int', value=None, default=None,
                          source='max_levels', prefix='-l', position=None, value_from=None),
                StepInput(id='output_steps', type='int', value=None, default=None,
                          source='steps_between_outputs', prefix='-i', position=None,
                          value_from=None),
                StepInput(id='time_steps', type='int', value=None, default=None,
                          source='time_steps', prefix='-t', position=None, value_from=None)],
        outputs=[StepOutput(id='clamr/clamr_stdout', type='stdout', value=None,
                            glob='clamr_stdout.txt'),
                 StepOutput(id='clamr/outdir', type='Directory', value=None,
                            glob='graphics_output/graph%05d.png'),
                 StepOutput(id='clamr/time_log', type='File', value=None,
                            glob='total_execution_time.log')],
        stdout='clamr_stdout.txt',
        stderr=None,
        workflow_id=WORKFLOW_GOLD.id
    ),
    Task(
        name='ffmpeg',
        base_command='ffmpeg -y',
        hints=[Hint(class_='DockerRequirement', params={'dockerFile': '# Dockerfile.clamr-ffmpeg\n# Developed on Chicoma @lanl\n# Patricia Grubel <pagrubel@lanl.gov>\n\nFROM debian:11\n\n\nRUN apt-get update && \\\n    apt-get install -y wget gnupg git cmake ffmpeg g++ make openmpi-bin libopenmpi-dev libpng-dev libpng16-16 libpng-tools imagemagick libmagickwand-6.q16-6 libmagickwand-6.q16-dev\n\nRUN git clone https://github.com/lanl/CLAMR.git\nRUN cd CLAMR && cmake . && make clamr_cpuonly\n', 'beeflow:containerName': 'clamr-ffmpeg'})], # noqa
        requirements=[],
        inputs=[StepInput(id='ffmpeg_input', type='Directory', value=None, default=None,
                          source='clamr/outdir', prefix='-i', position=2,
                          value_from='$("/graph%05d.png")'),
                StepInput(id='frame_rate', type='int', value=None, default=None,
                          source='frame_rate', prefix='-r', position=3, value_from=None),
                StepInput(id='frame_size', type='string', value=None, default=None,
                          source='frame_size', prefix='-s', position=4, value_from=None),
                StepInput(id='input_format', type='string', value=None, default=None,
                          source='input_format', prefix='-f', position=1, value_from=None),
                StepInput(id='output_file', type='string', value=None, default=None,
                          source='output_filename', prefix=None, position=6, value_from=None),
                StepInput(id='pixel_format', type='string', value=None, default=None,
                          source='pixel_format', prefix='-pix_fmt', position=5, value_from=None)],
        outputs=[StepOutput(id='ffmpeg/movie', type='File', value=None,
                            glob='$(inputs.output_file)'),
                 StepOutput(id='ffmpeg/ffmpeg_stderr', type='stderr', value=None,
                            glob='ffmpeg_stderr.txt')],
        stdout=None,
        stderr='ffmpeg_stderr.txt',
        workflow_id=WORKFLOW_GOLD.id)
]


TASKS_GOLD_VALIDATE_SCRIPT = [
    Task(
        name='clamr',
        base_command='/CLAMR/clamr_cpuonly',
        hints=[Hint(class_='DockerRequirement', params={'dockerFile': '# Dockerfile.clamr-ffmpeg\n# Developed on Chicoma @lanl\n# Patricia Grubel <pagrubel@lanl.gov>\n\nFROM debian:11\n\n\nRUN apt-get update && \\\n    apt-get install -y wget gnupg git cmake ffmpeg g++ make openmpi-bin libopenmpi-dev libpng-dev libpng16-16 libpng-tools imagemagick libmagickwand-6.q16-6 libmagickwand-6.q16-dev\n\nRUN git clone https://github.com/lanl/CLAMR.git\nRUN cd CLAMR && cmake . && make clamr_cpuonly\n', 'beeflow:containerName': 'clamr-ffmpeg'}), #noqa
               Hint(class_='beeflow:ScriptRequirement', params={'enabled': True, 'pre_script': 'echo "Before run"\n', 'post_script': 'echo "After run"\n'})], #noqa
        requirements=[],
        inputs=[StepInput(id='graphic_steps', type='int', value=None, default=None,
                          source='steps_between_graphics', prefix='-g', position=None,
                          value_from=None),
                StepInput(id='graphics_type', type='string', value=None, default=None,
                          source='graphics_type', prefix='-G', position=None, value_from=None),
                StepInput(id='grid_res', type='int', value=None, default=None,
                          source='grid_resolution', prefix='-n', position=None, value_from=None),
                StepInput(id='max_levels', type='int', value=None, default=None,
                          source='max_levels', prefix='-l', position=None, value_from=None),
                StepInput(id='output_steps', type='int', value=None, default=None,
                          source='steps_between_outputs', prefix='-i', position=None,
                          value_from=None),
                StepInput(id='time_steps', type='int', value=None, default=None,
                          source='time_steps', prefix='-t', position=None, value_from=None)],
        outputs=[StepOutput(id='clamr/clamr_stdout', type='stdout', value=None,
                            glob='clamr_stdout.txt'),
                 StepOutput(id='clamr/outdir', type='Directory', value=None,
                            glob='graphics_output/graph%05d.png'),
                 StepOutput(id='clamr/time_log', type='File', value=None,
                            glob='total_execution_time.log')],
        stdout='clamr_stdout.txt',
        stderr=None,
        workflow_id=WORKFLOW_GOLD.id
    ),
    Task(
        name='ffmpeg',
        base_command='ffmpeg -y',
        hints=[Hint(class_='DockerRequirement', params={'dockerFile': '# Dockerfile.clamr-ffmpeg\n# Developed on Chicoma @lanl\n# Patricia Grubel <pagrubel@lanl.gov>\n\nFROM debian:11\n\n\nRUN apt-get update && \\\n    apt-get install -y wget gnupg git cmake ffmpeg g++ make openmpi-bin libopenmpi-dev libpng-dev libpng16-16 libpng-tools imagemagick libmagickwand-6.q16-6 libmagickwand-6.q16-dev\n\nRUN git clone https://github.com/lanl/CLAMR.git\nRUN cd CLAMR && cmake . && make clamr_cpuonly\n', 'beeflow:containerName': 'clamr-ffmpeg'})], # noqa
        requirements=[],
        inputs=[StepInput(id='ffmpeg_input', type='Directory', value=None, default=None,
                          source='clamr/outdir', prefix='-i', position=2,
                          value_from='$("/graph%05d.png")'),
                StepInput(id='frame_rate', type='int', value=None, default=None,
                          source='frame_rate', prefix='-r', position=3, value_from=None),
                StepInput(id='frame_size', type='string', value=None, default=None,
                          source='frame_size', prefix='-s', position=4, value_from=None),
                StepInput(id='input_format', type='string', value=None, default=None,
                          source='input_format', prefix='-f', position=1, value_from=None),
                StepInput(id='output_file', type='string', value=None, default=None,
                          source='output_filename', prefix=None, position=6, value_from=None),
                StepInput(id='pixel_format', type='string', value=None, default=None,
                          source='pixel_format', prefix='-pix_fmt', position=5, value_from=None)],
        outputs=[StepOutput(id='ffmpeg/movie', type='File', value=None,
                            glob='$(inputs.output_file)'),
                 StepOutput(id='ffmpeg/ffmpeg_stderr', type='stderr', value=None,
                            glob='ffmpeg_stderr.txt')],
        stdout=None,
        stderr='ffmpeg_stderr.txt',
        workflow_id=WORKFLOW_GOLD.id)
]


TASKS_GOLD = [
    Task(
        name='clamr',
        base_command='/CLAMR/clamr_cpuonly',
        hints=[Hint(class_='DockerRequirement', params={'dockerFile': '# Dockerfile.clamr-ffmpeg\n# Developed on Chicoma @lanl\n# Patricia Grubel <pagrubel@lanl.gov>\n\nFROM debian:11\n\n\nRUN apt-get update && \\\n    apt-get install -y wget gnupg git cmake ffmpeg g++ make openmpi-bin libopenmpi-dev libpng-dev libpng16-16 libpng-tools imagemagick libmagickwand-6.q16-6 libmagickwand-6.q16-dev\n\nRUN git clone https://github.com/lanl/CLAMR.git\nRUN cd CLAMR && cmake . && make clamr_cpuonly\n', 'beeflow:containerName': 'clamr-ffmpeg'})], # noqa
        requirements=[],
        inputs=[StepInput(id='graphic_steps', type='int', value=None, default=None,
                          source='steps_between_graphics', prefix='-g', position=None,
                          value_from=None),
                StepInput(id='graphics_type', type='string', value=None, default=None,
                          source='graphics_type', prefix='-G', position=None, value_from=None),
                StepInput(id='grid_res', type='int', value=None, default=None,
                          source='grid_resolution', prefix='-n', position=None, value_from=None),
                StepInput(id='max_levels', type='int', value=None, default=None,
                          source='max_levels', prefix='-l', position=None, value_from=None),
                StepInput(id='output_steps', type='int', value=None, default=None,
                          source='steps_between_outputs', prefix='-i', position=None,
                          value_from=None),
                StepInput(id='time_steps', type='int', value=None, default=None,
                          source='time_steps', prefix='-t', position=None, value_from=None)],
        outputs=[StepOutput(id='clamr/clamr_stdout', type='stdout', value=None,
                            glob='clamr_stdout.txt'),
                 StepOutput(id='clamr/outdir', type='Directory', value=None,
                            glob='graphics_output/graph%05d.png'),
                 StepOutput(id='clamr/time_log', type='File', value=None,
                            glob='total_execution_time.log')],
        stdout='clamr_stdout.txt',
        stderr=None,
        workflow_id=WORKFLOW_GOLD.id
    ),
    Task(
        name='ffmpeg',
        base_command='ffmpeg -y',
        hints=[Hint(class_='DockerRequirement', params={'dockerFile': '# Dockerfile.clamr-ffmpeg\n# Developed on Chicoma @lanl\n# Patricia Grubel <pagrubel@lanl.gov>\n\nFROM debian:11\n\n\nRUN apt-get update && \\\n    apt-get install -y wget gnupg git cmake ffmpeg g++ make openmpi-bin libopenmpi-dev libpng-dev libpng16-16 libpng-tools imagemagick libmagickwand-6.q16-6 libmagickwand-6.q16-dev\n\nRUN git clone https://github.com/lanl/CLAMR.git\nRUN cd CLAMR && cmake . && make clamr_cpuonly\n', 'beeflow:containerName': 'clamr-ffmpeg'})], # noqa
        requirements=[],
        inputs=[StepInput(id='ffmpeg_input', type='Directory', value=None, default=None,
                          source='clamr/outdir', prefix='-i', position=2,
                          value_from='$("/graph%05d.png")'),
                StepInput(id='frame_rate', type='int', value=None, default=None,
                          source='frame_rate', prefix='-r', position=3, value_from=None),
                StepInput(id='frame_size', type='string', value=None, default=None,
                          source='frame_size', prefix='-s', position=4, value_from=None),
                StepInput(id='input_format', type='string', value=None, default=None,
                          source='input_format', prefix='-f', position=1, value_from=None),
                StepInput(id='output_file', type='string', value=None, default=None,
                          source='output_filename', prefix=None, position=6, value_from=None),
                StepInput(id='pixel_format', type='string', value=None, default=None,
                          source='pixel_format', prefix='-pix_fmt', position=5, value_from=None)],
        outputs=[StepOutput(id='ffmpeg/movie', type='File', value=None,
                            glob='$(inputs.output_file)'),
                 StepOutput(id='ffmpeg/ffmpeg_stderr', type='stderr', value=None,
                            glob='ffmpeg_stderr.txt')],
        stdout=None,
        stderr='ffmpeg_stderr.txt',
        workflow_id=WORKFLOW_GOLD.id)
]


WORKFLOW_NOJOB_GOLD = Workflow(
    name='cf',
    hints=[],
    requirements=[],
    inputs={InputParameter(id='infile', type='File', value='infile')},
    outputs={OutputParameter(id='ffmpeg_movie', type='File', value=None, source='ffmpeg/outfile'),
             OutputParameter(id='clamr_dir', type='File', value=None, source='clamr/outfile')},
    workflow_id=generate_workflow_id())


TASKS_NOJOB_GOLD = [
    Task(
        name='clamr',
        base_command='/clamr/CLAMR-master/clamr_cpuonly -n 32 -l 3 -t 5000 -i 10 -g 25 -G png',
        hints=[Hint(class_='DockerRequirement',
                    params={'dockerImageId': '/usr/projects/beedev/clamr/clamr-toss.tar.gz'})],
        requirements=[],
        inputs=[StepInput(id='infile', type='File', value=None, default='lorem.txt',
                          source='infile', prefix=None, position=1, value_from=None)],
        outputs=[StepOutput(id='clamr/outfile', type='stdout', value=None,
                            glob='graphics_output')],
        stdout='graphics_output',
        stderr=None,
        workflow_id=WORKFLOW_NOJOB_GOLD.id),
    Task(
        name='ffmpeg',
        base_command='ffmpeg -f image2 -i $HOME/graphics_output/graph%05d.png -r 12 -s 800x800 -pix_fmt yuv420p $HOME/CLAMR_movie.mp4', # noqa
        hints=[],
        requirements=[],
        inputs=[StepInput(id='infile', type='File', value=None, default='graphics_output',
                          source='clamr/outfile', prefix=None, position=1, value_from=None)],
        outputs=[StepOutput(id='ffmpeg/outfile', type='stdout', value=None,
                            glob='CLAMR_movie.mp4')],
        stdout='CLAMR_movie.mp4',
        stderr=None,
        workflow_id=WORKFLOW_NOJOB_GOLD.id)
]


if __name__ == '__main__':
    unittest.main()
