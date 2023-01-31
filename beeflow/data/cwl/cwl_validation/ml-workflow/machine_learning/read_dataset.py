"""Read Data Set."""
import pickle
import click
# import json
import pandas as pd
# import numpy as np
# from sklearn.linear_model import LinearRegression


@click.command()
@click.argument('y3', type=str)  # y3 is the input argument for path to dataset
def reader(y3):
    """Reader."""
    dataset = pd.read_csv(y3)

    print("this dataset", dataset)
    dataset['experience'].fillna(0, inplace=True)
    dataset['test_score'].fillna(dataset['test_score'].mean(), inplace=True)
    # Extracting rows (X-> independent variables and Y-> dependent/target variable)

    X = dataset.iloc[:, :3]   # Extracting first three columns from the dataset
    print('My X', X)

    Y = dataset.iloc[:, -1]  # Extracting last column from the dataset for target variable

    # Exporting X and Y as pickle files on to the disk
    pickle.dump(X, open("MyX.p", "wb"))
    pickle.dump(Y, open("MyY.p", "wb"))
    df1 = X.to_json()
    df2 = Y.to_json()


if __name__ == '__main__':
    reader(y3="")
# Ignores preserving code for now
# pylama:ignore=C0103,R1732,W0612
