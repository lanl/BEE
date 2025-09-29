#!/usr/bin/env python3
import argparse
import os
import importlib
import ast

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def scale(data_scaler, scaler_kwargs, X_train, X_test):
    if data_scaler:
        preprocessing_module = importlib.import_module("sklearn.preprocessing")
        scaling_fn = getattr(preprocessing_module, data_scaler)
        scaler = scaling_fn(**scaler_kwargs)
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
    return X_train, X_test

def main():
    parser = argparse.ArgumentParser(
        description="Split a CSV dataset into train/test and save as .npy files.")
    parser.add_argument(
        "--csv_path", type=str, required=True,
        help="Path to the input CSV file")
    parser.add_argument(
        "--features", type=str, nargs="+", required=True,
        help="Column names to use as features (X). Specify one or more.")
    parser.add_argument(
        "--target", type=str, required=True,
        help="Column name to use as target (Y).")
    parser.add_argument(
        "--test_size", type=float, default=0.2,
        help="Fraction of data to reserve for the test set (e.g. 0.25).")
    parser.add_argument(
        "--random_seed", type=int, default=None,
        help="Random seed for reproducibility.")
    parser.add_argument(
        "--data_path", type=str, required=True,
        help="Directory where x_train.npy, x_test.npy, y_train.npy, y_test.npy will be saved.")
    parser.add_argument(
        "--preprocess_info", type=str, required=True,
        help="stdout from the preprocessing step")
    parser.add_argument(
        "--data_scaler", type=str, default=None,
            help="Name of the sklearn scaling class")
    parser.add_argument(
        "--scaler_kwargs", type=str, default="{}",
        help="Optional keyword arguments for the scaling function")
    args = parser.parse_args()

    # Load data
    df = pd.read_csv(args.csv_path)
    df_first_3 = df.head(3)
    print(df_first_3)

    # Extract X and y
    X = df[args.features].values
    y = df[args.target].values

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=args.test_size,
        random_state=args.random_seed
    )

    # Scale the data if applicable
    data_scaler = args.data_scaler
    scaler_kwargs = ast.literal_eval(args.scaler_kwargs)
    X_train, X_test = scale(data_scaler, scaler_kwargs, X_train, X_test)

    # Ensure output directory exists
    os.makedirs(args.data_path, exist_ok=True)

    # Save
    np.save(os.path.join(args.data_path, "x_train.npy"), X_train)
    np.save(os.path.join(args.data_path, "x_test.npy"),  X_test)
    np.save(os.path.join(args.data_path, "y_train.npy"), y_train)
    np.save(os.path.join(args.data_path, "y_test.npy"),  y_test)

    print(f"Saved splits to {args.data_path!r}:")
    print("  - x_train.npy")
    print("  - x_test.npy")
    print("  - y_train.npy")
    print("  - y_test.npy")

if __name__ == "__main__":
    main()

