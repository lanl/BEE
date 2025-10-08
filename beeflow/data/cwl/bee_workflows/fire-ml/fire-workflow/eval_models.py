#!/usr/bin/env python3
import argparse
import os
import importlib

import numpy as np
from joblib import load
import ast
import json
from inspect import signature


def evaluate(y_test, y_pred, y_score, metrics_info):
    results = {}
    metrics_module = importlib.import_module("sklearn.metrics")

    for metric in metrics_info:
        name = metric["name"]
        params = metric.get("params", {})
        
        metric_fn = getattr(metrics_module, name)
        sig = signature(metric_fn)
        if "y_score" in sig.parameters:
            if y_score is None:
                results[name] = None
                continue
            result = metric_fn(y_test, y_score, **params)
        else:
            result = metric_fn(y_test, y_pred, **params)

        results[name] = result
    return results 


def main():
    parser = argparse.ArgumentParser(
        description="Run metrics on a given model.")
    parser.add_argument(
        "--data_path", type=str, required=True,
        help="Path to the training and testing datasets")
    parser.add_argument(
        "--model_dir_path", type=str, required=True,
        help="Path to the model")
    parser.add_argument(
        "--name",  type=str, required=True,
        help="Name of the model to use")
    parser.add_argument(
        "--metrics_info",  type=str, required=True,
        help="Dictionary of the metrics and their kwargs to use")
    parser.add_argument(
        "--metric_output_dir", type=str, required=True,
        help="Directory where the metrics output will be saved.")
    parser.add_argument(
        "--npy_output_dir", type=str, required=True,
        help="Directory where the predictions will be saved.")
    parser.add_argument(
        "--opt_info", type=str, required=True,
        help="stdout from the optimization step")
    args = parser.parse_args()


    x_test = np.load(args.data_path + "/x_test.npy")
    y_test = np.load(args.data_path + "/y_test.npy")

    clf = load(os.path.join(args.model_dir_path, args.name + ".joblib"))

    y_pred = clf.predict(x_test)

    try:
        y_score = clf.score(x_test, y_test)
    except AttributeError:
        y_score = None

    metrics_info = ast.literal_eval(args.metrics_info)
    results = evaluate(y_test, y_pred, y_score, metrics_info)
    results['model_score'] = y_score

    # Save metrics, predictions, and scores
    metric_output_dir = args.metric_output_dir
    os.makedirs(metric_output_dir, exist_ok=True)
    metrics_path = os.path.join(metric_output_dir, args.name + ".json")
    # Load existing data if the file exists
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = {}
    else:
        existing = {}

    existing.update(results)
    with open(metrics_path, 'w') as f:
        json.dump(existing, f, indent=4)

    np.save(os.path.join(args.npy_output_dir, args.name + "_y_pred.npy"), y_pred)


if __name__ == "__main__":
    main()
