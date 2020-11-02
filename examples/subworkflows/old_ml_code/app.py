from workflow.engine import GenericWorkflowEngine
from functools import wraps
# Importing the libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import numpy as np
# Importing the libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle

import numpy as np
from flask import Flask, request, jsonify, render_template
import pickle

# Define workflow instance
my_engine = GenericWorkflowEngine()


# Create modules called tasks that the workflow can call
def print_data(obj, eng):
    """Print the data found in the token."""
    print (obj.data)

def preprocess(obj,eng):


    dataset['experience'].fillna(0, inplace=True)

    dataset['test_score'].fillna(dataset['test_score'].mean(), inplace=True)

    X = dataset.iloc[:, :3]

    # Converting words to integer values
    def convert_to_int(word):
        word_dict = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
                     'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'zero': 0, 0: 0}
        return word_dict[word]

    X['experience'] = X['experience'].apply(lambda x: convert_to_int(x))
    obj.tempX=X


def train(obj,eng):
    y = dataset.iloc[:, -1]

    # Splitting Training and Test Set
    # Since we have a very small dataset, we will train our model with all availabe data.
    obj.tempY=y
    from sklearn.linear_model import LinearRegression
    regressor = LinearRegression()

    # Fitting model with trainig data
    regressor.fit(obj.tempX, obj.tempY)

    # Saving model to disk
    pickle.dump(regressor, open('model.pkl', 'wb'))
    obj.model=regressor


def predict(obj,eng):
    # Loading model to compare the results
    #model = pickle.load(open('model.pkl', 'rb'))
    model=obj.model
    print(model.predict([[2, 9, 6]]))
    # argparser --


def deploy(obj,eng):
    print("Deployment done")
    obj.app=app
    model = obj.model


    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/predict', methods=['POST'])
    def predict():
        '''
        For rendering results on HTML GUI
        '''
        int_features = [int(x) for x in request.form.values()]
        final_features = [np.array(int_features)]
        prediction = model.predict(final_features)

        output = round(prediction[0], 2)

        return render_template('index.html', prediction_text='Employee Salary should be $ {}'.format(output))

    @app.route('/predict_api', methods=['POST'])
    def predict_api():
        '''
        For direct API calls trought request
        '''
        data = request.get_json(force=True)
        prediction = model.predict([np.array(list(data.values()))])

        output = prediction[0]
        return jsonify(output)

'''
# Define functions that need additional parameters, e.g. number_to_add
def add_data(number_to_add):
    """Add number_to_add to obj.data."""
    @wraps(add_data)
    def _add_data(obj, eng):
        obj.data += number_to_add

    return _add_data
'''

# Define workflow outline
my_workflow_definition = [
    #add_data(1),
    print_data,
    preprocess,
    train,
    predict,
    deploy
]

# Create object instances called tokens
class MyObject(object):
    def __init__(self, data, tempX, tempY,app):
        self.data = data
        self.tempX=tempX
        self.tempY=tempY
        self.app=app



# Run engine to generate results
#my_object0 = MyObject(np.array([0, 1, 2]))
#my_object1 = MyObject(np.array([2, 3, 4]))
global dataset
dataset = pd.read_csv('hiring.csv')
tempX=None
tempY=None
mymodel=None
app = Flask(__name__)
my_object0 = MyObject(dataset,tempX,tempY,app)

my_engine.callbacks.replace(my_workflow_definition)

# Several runs
my_engine.process([my_object0])



if __name__ == "__main__":
    app.run(debug=True)
