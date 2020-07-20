
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
## Import dataset
dataset = pd.read_csv('hiring.csv')


## Replace null values 
dataset['experience'].fillna(0, inplace=True)
## Replace na with true
dataset['test_score'].fillna(dataset['test_score'].mean(), inplace=True)

## Extracting rows
X = dataset.iloc[:, :3]

#Converting nominal values into integer values
def convert_to_int(word):
    word_dict = {'one':1, 'two':2, 'three':3, 'four':4, 'five':5, 'six':6, 'seven':7, 'eight':8,
                'nine':9, 'ten':10, 'eleven':11, 'twelve':12, 'zero':0, 0: 0}
    return word_dict[word]

## Applying lambda x to column in X dataframe
X['experience'] = X['experience'].apply(lambda x : convert_to_int(x))


## Extract all rows for training
y = dataset.iloc[:, -1]

#Splitting Training and Test Set
#As the size of dataset is small we  train our model with all availabe data

from sklearn.linear_model import LinearRegression
regressor = LinearRegression()

#Fitting model with trainig data
regressor.fit(X, y)
#To retrieve the intercept:
print(regressor.intercept_)
#For retrieving the slope:
print(regressor.coef_)

# Saving model to disk (serializing it using pickle) and storing it as model.pkl
pickle.dump(regressor, open('model.pkl','wb'))

# Loading model to compare the results
model = pickle.load(open('model.pkl','rb'))
print(model.predict([[2, 9, 6]]))
