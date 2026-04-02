#!/usr/bin/env python3
import argparse
import os
import importlib
import json

import numpy as np
import pandas as pd
from joblib import dump
import ast
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report


def main():
    parser = argparse.ArgumentParser(
            description="Find the best hyperparameters for a given model.")
    parser.add_argument(
            "--data_path", type=str, required=True,
            help="Path to the training and testing datasets")
    parser.add_argument(
            "--name",  type=str, required=True,
            help="Name of the model to use")
    parser.add_argument(
            "--sk_class", type=str, required=True,
            help="sklearn class")
    parser.add_argument(
            "--param_grid", type=str, required=True,
            help="JSON string of parameters to use with GridSearchCV")
    parser.add_argument(
        "--model_dir_path", type=str, required=True,
        help="Directory where the best fit estimators will be saved.")
    parser.add_argument(
        "--metric_output_dir", type=str, required=True,
        help="Directory where evaluation metrics are stored")
    parser.add_argument(
        "--split_info", type=str, required=True,
        help="stdout from the splitting step")
    parser.add_argument(
            "--model_kwargs", type=str, default="{}",
            help="Optional keyword arguments for the model")
    parser.add_argument(
            "--gridsearch_kwargs", type=str, default="{}",
            help="Optional keyword arguments for GridSearchCV")
    args = parser.parse_args()

    # Load training data
    x_train = np.load(args.data_path + "/x_train.npy")
    y_train = np.load(args.data_path + "/y_train.npy")


    # Import model
    module_name, class_name = args.sk_class.rsplit(".", 1)
    module = importlib.import_module(module_name)
    klass = getattr(module, class_name)

    # Define model arguments and gridsearch argumentsand paramters
    model_kwargs = ast.literal_eval(args.model_kwargs)
    param_grid = ast.literal_eval(args.param_grid)
    gridsearch_kwargs = ast.literal_eval(args.gridsearch_kwargs)

    # Get the instance of the best fit estimator
    model = klass(**model_kwargs)
    clf = GridSearchCV(model, param_grid, **gridsearch_kwargs)
    clf.fit(x_train, y_train)

    # Save the model
    name = args.name
    os.makedirs(args.model_dir_path, exist_ok=True)
    dump(clf, os.path.join(args.model_dir_path, name + ".joblib"))

    # Get and save metric info
    metric_output_dir = args.metric_output_dir
    best_params = clf.best_params_
    print(f"Best parameters for {name}: {best_params}")

    cv_results = clf.cv_results_
    best_index = clf.best_index_

    metrics = {
            'best_params': best_params,
            'mean_fit_time': float(cv_results['mean_fit_time'][best_index]),
            'std_fit_time': float(cv_results['std_fit_time'][best_index]),
            'mean_score_time': float(cv_results['mean_score_time'][best_index]),
            'std_score_time': float(cv_results['std_score_time'][best_index]),
    }
    os.makedirs(metric_output_dir, exist_ok=True)
    metrics_path = os.path.join(metric_output_dir, args.name + ".json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)

    # Save CV Results
    df = pd.DataFrame(cv_results)
    df.to_csv(os.path.join(metric_output_dir, args.name + "_cv_results.csv"), index=False)

if __name__ == "__main__":
    main()
