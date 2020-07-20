## Prerequisites

Download the following packages:
Scikit Learn, Pandas (for Machine Leraning Model) and Flask (for API)

## Repo Structure
Four major parts :

1. model.py - This contains code for the Machine Learning model to make a prediction on employee salaries absed on trainining data as stored in '50_Startup.csv' file
2. app.py - This contains Flask APIs that receives employee details through a GUI or API calls, computes the predicted value based on our model and returns it
3. request.py - This uses requests module to call APIs already defined in app.py and dispalys the returned value
4. templates - Contains the HTML template to allow user to enter employee detail and displays the predicted employee salary

## Running the project


Create the machine learning model by running below command -

python model.py

This creates a serialized version of the model into a file model.pkl

Run app.py using below command to start Flask API
python app.py
By default, flask runs on http://127.0.0.1:5000/.

Navigate to URL http://127.0.0.1:5000/
