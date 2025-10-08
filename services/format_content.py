import pandas as pd
import numpy as np
import json
import os
from services.hash import make_compact_uid_b32
import re


def coerce_bool_option(value):
    if value == 0:
        return None
    else:
        return 0


def format_config(experiment_folder, config):
    if config["name"] != "None":
        file_path = os.path.join(experiment_folder, config["name"])
        config_type = config["name"].split(".")[-1]
        if config_type == "json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if config["options"]["flatten"]:
                data = pd.json_normalize(data, sep="_").to_dict(orient="records")[0]
        elif config_type == "xlsx" or config_type == "xlsm":
            data = pd.read_excel(file_path, sheet_name=config["sheet"]).to_dict(orient="records")
        elif config_type == "csv":
            sep = (config.get("options", {}) or {}).get("sep", ",")
            sep = "\t" if sep == "\\t" else sep
            data = pd.read_csv(file_path, sep=sep).to_dict(orient="records")
        else:
            raise ValueError(f"Unsupported config type: {config_type}")
    return data


def format_metrics(experiment_folder, metrics):
    metrics_data = {}
    if metrics["name"] != "None":
        file_path = os.path.join(experiment_folder, metrics["name"])
        metrics_type = metrics["name"].split(".")[-1]
        if metrics_type == "xlsx" or metrics_type == "xlsm":
            df = pd.read_excel(file_path, sheet_name=metrics["sheet"], header=coerce_bool_option(metrics["options"]["header"]))
        elif metrics_type == "csv":
            df = pd.read_csv(file_path, header=coerce_bool_option(metrics["options"]["header"]))
        else:
            raise ValueError(f"Unsupported metrics type: {metrics_type}")

        metrics_columns = {}

        for col in metrics["options"]["selected_cols"]:
            if metrics["options"]["has_time"]==1:
                if col == metrics["options"]["time_col"]:
                    metrics_data["x_axis"] = df[col].to_list()
                else: 
                    metrics_columns[col] = df[col].to_list()
            else:
                metrics_columns[col] = df[col].to_list()

        metrics_data["columns"] = metrics_columns

    return metrics_data


def format_results(experiment_folder, results):
    results_data = {}
    if results["name"] != "None":
        file_path = os.path.join(experiment_folder, results["name"])
        results_type = results["name"].split(".")[-1]
        if results_type == "xlsx" or results_type == "xlsm":
            data_ = pd.read_excel(file_path, sheet_name=results["sheet"], header=None).to_dict(orient="records")
            data = {e[0]: e[1] for e in data_}

        elif results_type == "csv":
            sep = (results.get("options", {}) or {}).get("sep", ",")
            sep = "\t" if sep == "\\t" else sep
            data_ = pd.read_csv(file_path, sep=sep, header=None).to_dict(orient="records")
            data = {e[0]: e[1] for e in data_}

        elif results_type == "json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported results type: {results_type}")
        
        results_data = {}

        for k, v in data.items():
            results_data[k] = v

    return results_data


def format_raw_data(experiment_folder, raw_data):
    files = {}
    if raw_data["name"] != "None":
        experiment_name = experiment_folder.split("/")[-1]
        file_path = os.path.join(experiment_folder, raw_data["name"])
        if os.path.isfile(file_path):
            file = {
                'source_path': file_path,
                'new_name': make_compact_uid_b32(experiment_name) + "-" + raw_data["name"],
                'minio_folder':  raw_data["name"].split(".")[0],
            }
            files[raw_data["name"]] = file

        elif os.path.isdir(file_path):
            for f in raw_data["files"]:
                file = {
                    'source_path': os.path.join(file_path, f),
                    'new_name': make_compact_uid_b32(experiment_name) + "-" + f,
                    'minio_folder':  f.split(".")[0],
                }
                files[f] = file
        else:
            raise ValueError(f"Raw data file or folder not found: {file_path}")

    return files