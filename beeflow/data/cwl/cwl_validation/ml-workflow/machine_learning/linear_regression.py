"""Linear Regression."""
import json
import pickle
import click
import numpy as np
from sklearn.linear_model import LinearRegression


@click.command()
@click.argument('x1', type=int)   # Enter number of iteration
def reg(x1):
    """Linear Regression."""
    X = pickle.load(open('/home/bee/cwl2/MyX.p', 'rb'))
    Y = pickle.load(open('/home/bee/cwl2/MyY.p', 'rb'))

    X = X.values

    print("My pickle X is", X)
    Y = Y.values
    print("My pickle Y is", Y)
    m = []
    y_in = []
    for i in range(x1):
        reg = LinearRegression().fit(X, Y)

        pickle.dump(reg, open('mymodel.p', 'wb'))
        m.append(reg.coef_)
        y_in.append(reg.intercept_)
        # m, y_in = reg.coef_, reg.intercept_

    average_slope = np.mean(m)
    average_y_intercept = np.mean(y_in)
    m_list = average_slope.tolist()
    m_json = json.dumps(m_list)
    y_in_list = average_y_intercept.tolist()
    y_in_json = json.dumps(y_in_list)

    print('Learning regression line parameters.')
    print(average_slope, average_y_intercept)  # model parameters i.e. slope and y-intercept


if __name__ == '__main__':
    reg(x1=1)
# Ignores preserving code for now
# pylama:ignore=C0103,R1732,W0612,W0621
