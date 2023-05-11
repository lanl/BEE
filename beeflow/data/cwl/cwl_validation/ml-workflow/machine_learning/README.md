
## Prerequisites

Download the following packages:
Scikit Learn, Pandas (for Machine Leraning Model) and  CWL-runner

## Install CWL Runner
pip install cwlref-runner

## Objective: Write a CWL workflow tool for different Machine Learning algorithms (Regression and Decision Tree) 
###### Workflow is described in four Steps:
Four steps: Each step corresponds to a machine learning stage and/or machine learning model with it’s respective CWL tool description
Each step (tool) references to a Python script written to preprocess input dataset, execute ML models, and make prediction
Execution order between intertwined steps of a workflow is determined by the connections between steps

## Machine learning goal: Prediction on Employee’s salary based on interview score, test score, experience

## Repo Structure
Major parts :
1. read_dataset.py: Python script to input dataset (hiring1.txt) and preprocess columns
2. read_dataset_tool.cwl: CWL tool referencing read_dataset.py. Takes input file path as input parameter
3. linear_regression.py: Python script for Linear Regression model, trains the model based on preprocessed input dataset and dumps the model's pickle file
4. regress_tool.cwl: References linear_regression.py, takes number of iterations as input parameter
5. linear_regress_output.txt: Contains regression line parameters X and Y
6. decision_tree.py: Script for Decision Tree model, trains the model based on preprocessed input dataset and dumps the model's pickle file
7. decision_tree_output.txt: Contains decision tree model parameters 
8. decision_tree_tool.cwl: References decision_tree.py, takes number of iterations as input parameter
9. predict_code.py: Script for importing regression and decision tree models and returning the output (expected salary of candidate)
10. predict_tool.cwl: References predict_code.py, takes three input parameters for testing (interview score, test score, experience(years) )
11. machinelearning_pipeline.cwl: This tool embeds all the above mentioned tools under one hood. Takes 4 input parameters (input file directory path, interview score, test score, experience)
12. expectedValue.txt: Contains output (expected salary of candidate) from both ML models in 


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




![GitHub output](/examples/subworkflows/machine_learning/out.PNG)

