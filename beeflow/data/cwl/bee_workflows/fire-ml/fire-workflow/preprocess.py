#!/usr/bin/env python3
import argparse
import os
import importlib
import joblib

import pandas as pd
import ast


def main():
    parser = argparse.ArgumentParser(
            description="Preprocess a CSV dataset")
    parser.add_argument(
        "--original_csv_path", type=str, required=True,
        help="Path to the input CSV file")
    parser.add_argument(
         "--drop_filters", type=str, nargs="*",
         help="List of column=value pairs; any matching rows will be removed.")
    parser.add_argument(
        "--encode_cols", type=str, nargs="+", required=True,
        help="Names of the columns to encode")
    parser.add_argument(
        "--keep_cols", type=str, nargs="+", required=True,
        help="Names of the columns that aren't encoded but should be kept")
    parser.add_argument(
        "--name",  type=str, required=True,
        help="Name of the encoder to use")
    parser.add_argument(
        "--csv_path", type=str, required=True,
        help="Path where the preprocessed csv will be saved")
    parser.add_argument(
        "--encoder_path", type=str, required=True,
        help="Path where the encoder will be saved")
    parser.add_argument(
        "--encoder_kwargs", type=str, default="{}",
        help="Optional keyword arguments for the encoder")
    args = parser.parse_args()

    # Load data
    df = pd.read_csv(args.original_csv_path)

    # Drop filters
    if args.drop_filters:
        for filt in args.drop_filters:
            try:
                col, raw_val = filt.split("=", 1)
            except ValueError:
                raise ValueError(f"Invalid filter '{filt}'; must be col=value")
            val = ast.literal_eval(raw_val)
            df = df[df[col] != val]
        df = df.reset_index(drop=True)

    # Import encoder
    preproc_module = importlib.import_module("sklearn.preprocessing")
    encoding_fn = getattr(preproc_module, args.name)

    # Define encoder arguments
    encoder_kwargs = ast.literal_eval(args.encoder_kwargs)

    # Encode the data
    encoder = encoding_fn(**encoder_kwargs)
    encode_cols = args.encode_cols
    encoded_array = encoder.fit_transform(df[encode_cols])
    encoded_df = pd.DataFrame(encoded_array, columns=encoder.get_feature_names_out(encode_cols))
    final_df = pd.concat([df[args.keep_cols], encoded_df], axis=1)

    # Ensure output directories exist
    os.makedirs(os.path.dirname(args.csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(args.encoder_path), exist_ok=True)

    # Save the csv and the encoder
    final_df.to_csv(args.csv_path, index=False)

    encoder_bundle = {
        "encoder": encoder,
        "encode_cols": encode_cols
    }
    joblib.dump(encoder_bundle, args.encoder_path)


if __name__ == "__main__":
    main()

