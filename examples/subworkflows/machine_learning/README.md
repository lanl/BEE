### In this example, we execute two different Machine Learning algorithms (Regression and Decision Tree) in the CWL workflow

###### Objective: Prediction on Employee’s salary based on interview score, test score, experience
###### Workflow is described in four Steps:
Four steps: Each step corresponds to a machine learning stage and/or machine learning model with it’s respective CWL tool description
Each step (tool) references to a Python script written to preprocess input dataset, execute ML models, and make prediction
Execution order between intertwined steps of a workflow is determined by the connections between steps



###### Testing Environment: Fedora 32 VM
###### Interpreter used: CWL-Runner 
###### ML Models used: 
Linear Regression and Decision Tree Classifier
Python package: Scikit learn


##### Sequence of Commands:
1. To execute machine learning workflow with both algorithms
* cwl-runner -- validate machinelearning_pipeline.cwl “/xx/xx/hiring1.txt” -- interviewscore 5 -- testscore 3 -- experience 3 -- iterations 50 [OK]
* cwl-runner machinelearning_pipeline.cwl --experience 5 --interview 4 --test 3 --iterations 1 --datasetpath /xx/xx/hiring1.txt [xx=directory path]
* cwl-runner --debug machinelearning_pipeline.cwl.cwl “/xx/xx/hiring1.txt” [Debug ?]

2. Breakdown of commands for running each CWL tool sequentially (Alternative approach to No.1)
* cwl-runner read_dataset_tool.cwl -x /xx/xx/xx/hiring1.txt  [Read input dataset, xx is directory path]
* cwl-runner regress_tool.cwl -x 1        [x is the number of iterations]
* cwl-runner decision_tree_tool.cwl -x 1  [x is the number of iterations]
* cwl-runner predict_tool.cwl -x 5 -y 6 -z 8 referenced to predict_code.py   [x,y,z correspond to interview score, testscore, and experience]

3. View Expected Outputs:
* cat expectedValue.txt
![GitHub output]()
Format: ![.PNG](url)
