## Sample CWL Pipeline for testing purpose with CWL-Runner tool

This directory contains a sample CWL pipeline that makes use of adding two numbers followed by multiplication. Interpretor used: CWL-Runner

### Prerequisites

1. CWL tool implementation

Installing the official package using pip (this will also install 'cwltool' package as well):
```
pip install cwl-runner
```
OR from Source package as follows:
```
git clone https://github.com/common-workflow-language/cwltool.git
cd cwltool && python setup.py install
cd cwl-runner && python setup.py install
```

### Run CWL Pipeline on the Command Line

First validate cwl file for any CWL syntax errors:
```
cwl-runner --validate add_multiply_example_workflow.cwl --num1 20 --num2 50
```
Simple Command:
```
cwl-runner add_multiply_example_workflow.cwl --num1 20 --num2 50
```
