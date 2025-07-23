#!/usr/bin/env python3
import argparse
import os
import importlib

import numpy as np
import pandas as pd
from joblib import load
import ast
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt



def main():
    parser = argparse.ArgumentParser(
        description="Find the permutation importance for feature evaluation.")
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
        "--features", type=str, nargs="+", required=True,
        help="Feature names.")
    parser.add_argument(
        "--output_format", type=str, required=True,
        help="Format to save the dataframe as. This should be of the form to_csv, to_latex")
    parser.add_argument(
        "--dataframe_name", type=str, required=True,
        help="name of the output file for the dataframe.")
    parser.add_argument(
        "--output_dir", type=str, required=True,
        help="Directory where the outputs should be saved")
    parser.add_argument(
        "--opt_info", type=str, required=True,
        help="stdout from the optimization step")
    parser.add_argument(
        "--importance_kwargs", type=str, default="{}",
        help="Optional keyword arguments for the permutation importance function")
    parser.add_argument(
        "--output_kwargs", type=str, default="{}",
        help="Optional keyword arguments for the dataframe output")
    args = parser.parse_args()

    x_test = np.load(args.data_path + "/x_test.npy")
    y_test = np.load(args.data_path + "/y_test.npy")

    clf = load(os.path.join(args.model_dir_path, args.name + ".joblib"))

    importance_kwargs = ast.literal_eval(args.importance_kwargs)
    result = permutation_importance(clf, x_test, y_test, **importance_kwargs)

    importance = pd.DataFrame(
            {"importance_mean": result["importances_mean"],
             "importance_std": result["importances_std"]},
             index=args.features
    )

    importance["importance_mean"].sort_values(
            ascending=False
    ).plot(figsize=(15, 5), kind="bar", yerr=importance["importance_std"])

    name = args.name
    no_underscores = name.replace("_", " ")
    formal_name = no_underscores.title()
    plt.title(f"{formal_name} Permutation Feature Importance")
    plt.ylabel("Performance drop (R2)")
    plt.subplots_adjust(bottom=0.25)

    # Save the plot
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, args.name + "_importances.png")
    plt.savefig(plot_path)

    # Save the dataframe
    output_format = args.output_format
    output_kwargs = ast.literal_eval(args.output_kwargs)
    df_path = os.path.join(args.output_dir, args.dataframe_name)
    getattr(importance, output_format)(df_path, **output_kwargs)


if __name__ == "__main__":
    main()

