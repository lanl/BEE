#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
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
        "--encoder_path", type=str, required=True,
        help="Path to the encoder")
    parser.add_argument(
        "--target", type=str, required=True,
        help="Name of the column to retrieve categories for")
    parser.add_argument(
        "--name", type=str, required=True,
        help="Name of the model that predicted the values")
    parser.add_argument(
        "--matrix_output_dir", type=str, required=True,
        help="Directory where the matrix will be saved.")
    parser.add_argument(
        "--display_kwargs", type=str, default="{}",
        help="Optional keyword arguments for the confusion matrix display function")
    parser.add_argument(
        "--eval_info", type=str, required=True,
        help="stdout from the evaluation step")
    args = parser.parse_args()


    name = args.name
    y_test = np.load(args.data_path + "/y_test.npy")
    y_pred = np.load(args.data_path + "/" + name + "_y_pred.npy")

    bundle = joblib.load(args.encoder_path)
    encoder = bundle["encoder"]
    encode_cols = bundle["encode_cols"]

    if args.target not in encode_cols:
        print(f"Column '{args.target}' not found in encode_cols: {encode_cols}")
        return

    index = encode_cols.index(args.target)
    categories = None
    no_underscores = name.replace("_", " ")
    formal_name = no_underscores.title()
    display_kwargs = ast.literal_eval(args.display_kwargs)
    matrix_output_dir = args.matrix_output_dir
    os.makedirs(matrix_output_dir, exist_ok=True)
    matrix_path = os.path.join(matrix_output_dir, name + "_matrix.png")
    try:
        categories = encoder.categories_[index]
        print(f"Categories for column '{args.target}': {categories}")
    except AttributeError:
        print("The encoder does not have 'categories_' attribute.")
    except IndexError:
        print(f"Invalid index {index} for column '{args.target}'.")
    finally:
        disp = ConfusionMatrixDisplay.from_predictions(
                y_test,
                y_pred,
                display_labels=categories,
                **display_kwargs
        )
        plt.title(formal_name)
        plt.savefig(matrix_path)

if __name__ == "__main__":
    main()
