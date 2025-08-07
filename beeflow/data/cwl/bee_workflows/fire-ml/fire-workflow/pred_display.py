#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
from sklearn.metrics import PredictionErrorDisplay
import numpy as np
import joblib
import ast
import os



def main():
    parser = argparse.ArgumentParser(
        description="Create a confusion matrix")
    parser.add_argument(
        "--data_path", type=str, required=True,
        help="Path to the y true and predicted values")
    parser.add_argument(
        "--name", type=str, required=True,
        help="Name of the model that predicted the values")
    parser.add_argument(
        "--pred_display_output_dir", type=str, required=True,
        help="Directory where the prediction error display will be saved.")
    parser.add_argument(
        "--display_kwargs", type=str, default="{}",
        help="Optional keyword arguments for the prediction error display function")
    parser.add_argument(
        "--eval_info", type=str, required=True,
        help="stdout from the evaluation step")
    args = parser.parse_args()

    name = args.name
    y_test = np.load(args.data_path + "/y_test.npy")
    y_pred = np.load(args.data_path + "/" + name + "_y_pred.npy")

    display_kwargs = ast.literal_eval(args.display_kwargs)
    pred_display_output_dir = args.pred_display_output_dir
    os.makedirs(pred_display_output_dir, exist_ok=True)
    display_path = os.path.join(pred_display_output_dir, name + "_pred_err.png")

    disp = PredictionErrorDisplay.from_predictions(y_test, y_pred, **display_kwargs)
    no_underscores = name.replace("_", " ")
    formal_name = no_underscores.title()
    plt.title(formal_name)
    plt.subplots_adjust(left=0.15)
    plt.savefig(display_path)


if __name__ == "__main__":
    main()

