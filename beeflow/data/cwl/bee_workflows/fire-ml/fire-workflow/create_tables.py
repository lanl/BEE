#!/usr/bin/env python3
import argparse
import os
import json
import pandas as pd
import ast


def extract_model_metrics(directory):
    data = []

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as f:
                metrics = json.load(f)
                model_name = filename.rsplit('.', 1)[0]
                row = {'model': model_name}
                row.update(metrics)
                data.append(row)

    df = pd.DataFrame(data)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Creat a table for a directory of files.")
    parser.add_argument(
        "--data_path", type=str, required=True,
        help="Path to the directory of json files")
    parser.add_argument(
        "--output_format", type=str, required=True,
        help="Format to save the dataframe as. This should be of the form to_csv, to_latex")
    parser.add_argument(
        "--output_name", type=str, required=True,
        help="name of the output file.")
    parser.add_argument(
        "--metric_output_dir", type=str, required=True,
        help="Directory where the output file should be saved.")
    parser.add_argument(
        "--eval_info", action='append', type=str,
        help="stdout from the evaluation step")
    parser.add_argument(
        "--output_kwargs", type=str, default="{}",
        help="Optional keyword arguments for the dataframe output")
    args = parser.parse_args()

    directory_path = args.data_path
    df_metrics = extract_model_metrics(directory_path)

    output_path = os.path.join(args.metric_output_dir, args.output_name)
    output_format = args.output_format
    output_kwargs = ast.literal_eval(args.output_kwargs)
    getattr(df_metrics, output_format)(output_path, **output_kwargs)

    print(f"Table saved to: {output_path}")


if __name__ == "__main__":
    main()

