import click
import json
import pickle
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn import metrics


@click.command()
@click.argument('e', type=float)
@click.argument('i',type=float)
@click.argument('t',type=float)
def pred(e,i,t):

    regression_model=pickle.load(open('/home/bee/cwl2/mymodel.p','rb')) ## Import Linear Regression model
    dt_model=pickle.load(open('/home/bee/cwl2/clf1.p','rb')) ## Import Decision Tree classifier model
    predict_linear_regression=regression_model.predict([[e,i,t]])
    predict_linear_regression_list=predict_linear_regression.tolist()
    predict_linear_regression_json_str=json.dumps(predict_linear_regression_list)

    predict_decision_tree=dt_model.predict([[e,i,t]])
    predict_decision_tree_list = predict_decision_tree.tolist()
    predict_decision_tree_json_str = json.dumps(predict_decision_tree_list)

    print("Expected Salary from Regression is $",predict_linear_regression)
    print("Expected Salary from DT is $", predict_decision_tree)


    click.echo(json.dumps({'Predicted Salary (S) by Regression and DT Model': (predict_linear_regression_json_str,predict_decision_tree_json_str)}))



if __name__ == '__main__':
    pred()


