"""Decision Tree."""
# import json
import pickle
import click
# import numpy as np
# from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier
# from sklearn.model_selection import train_test_split
# from sklearn import metrics


@click.command()
@click.argument('x1', type=int)
def reg(x1):
    """Reqression."""
    # Import X and Y datasets
    X = pickle.load(open('/home/bee/cwl2/MyX.p', 'rb'))
    Y = pickle.load(open('/home/bee/cwl2/MyY.p', 'rb'))

    X = X.values

    print("My pickle X is", X)
    Y = Y.values
    print("My pickle Y is", Y)
    for i in range(x1):
        clf = DecisionTreeClassifier()
        clf1 = clf.fit(X, Y)
    print("Decision tree parameters")
    print(clf1)
    pickle.dump(clf1, open('clf1.p', 'wb'))


if __name__ == '__main__':
    reg(x1=1)
# Ignores preserving code for now
# pylama:ignore=C0103,R1732,W0612,W0621
