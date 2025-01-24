"""Cat Grep Tar driver for CWL generator."""
from beeflow.common.cwl.workflow import Task, Input, Output, Workflow


def main():
    """Recreate the COMD workflow."""
    cat = Task(name="cat",
               base_command="cat",
               stdout="cat.txt",
               stderr="cat.err",
               inputs=[Input('input_file', 'File', "lorem.txt", position=1)],
               outputs=[Output('contents', 'stdout'),
                        Output('cat_stderr', 'stderr', source='cat/cat_stderr')])

    grep0 = Task(name="grep0",
                 base_command="grep",
                 stdout="occur0.txt",
                 inputs=[Input("word0", "string", "Vivamus", position=1),
                         Input('text_file', 'File', "cat/contents", position=2)],
                 outputs=[Output('occur', 'stdout')])

    grep1 = Task(name="grep1",
                 base_command="grep",
                 stdout="occur1.txt",
                 inputs=[Input("word1", "string", "pulvinar", position=1),
                         Input('text_file', 'File', "cat/contents", position=2)],
                 outputs=[Output('occur', 'stdout')])

    tar = Task(name="tar",
               base_command="grep",
               stdout="occur1.txt",
               inputs=[Input("tarball_fname", "string", "tarball_fname", position=1, prefix='-cf'),
                       Input('file0', 'File', "grep0/occur", position=2),
                       Input('file1', 'File', "grep1/occur", position=3)],
               outputs=[Output('tarball', 'File', glob="$(inputs.tarball_fname)",
                        source="tar/tarball")])

    workflow = Workflow("comd", [cat, grep0, grep1, tar])
    workflow.write(".")


if __name__ == "__main__":
    main()
