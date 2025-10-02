from __future__ import annotations
import sacred
from sacred import Experiment
from sacred.observers import MongoObserver
import numpy as np
import os
import pandas as pd
import csv
from typing import Any, Dict
import services.format_content as fc
from services.mongo_conn import build_mongo_url_from_payload


def send_experiment(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Validate presence of top-level domains
    if not isinstance(payload, dict):
        return {"ok": False, "message": "Invalid payload"}

    data_payload = payload.get("experiment", {}) or {}
    mongo_payload = payload.get("mongo", {}) or {}
    experiment_folder = data_payload.get("folder", "")
    experiment_name = (data_payload.get("name") or "").strip()
    selectors = data_payload.get("selectors", {}) or {}
    config = selectors.get("config", {}) or {}
    metrics = selectors.get("metrics", {}) or {}
    results = selectors.get("results", {}) or {}
    raw_data = selectors.get("raw_data", {}) or {}
    artifacts = selectors.get("artifacts", {}) or {}

    print(f"config: {fc.format_config(experiment_folder, config)}\n")
    config = fc.format_config(experiment_folder, config)
    print(f"results: {fc.format_results(experiment_folder, results)}\n")
    results = fc.format_results(experiment_folder, results)
    print(f"raw_data: {fc.format_raw_data(experiment_folder, raw_data)}\n")
    raw_data = fc.format_raw_data(experiment_folder, raw_data)
    print(f"artifacts: {fc.format_raw_data(experiment_folder, artifacts)}\n")
    artifacts = fc.format_raw_data(experiment_folder, artifacts)
    print(f"metrics: {fc.format_metrics(experiment_folder, metrics)}\n")
    metrics = fc.format_metrics(experiment_folder, metrics)

    # --- Build Mongo connection using shared helper ---
    mongo_payload = payload.get("mongo", {}) or {}
    mongo_url, mongo_db = build_mongo_url_from_payload(mongo_payload)


    ex = Experiment(experiment_name, save_git_info=True)
    # Attach Mongo observer
    try:
        ex.observers.append(MongoObserver(url=mongo_url, db_name=mongo_db))
    except Exception:
        pass


    @ex.main
    def run(_run):
        if 'x_axis' in metrics:
            x_axis = metrics['x_axis']

            for column in metrics['columns']:
                for i, value in enumerate(metrics['columns'][column]):
                    _run.log_scalar(column, value, step=x_axis[i])
        else:
            for column in metrics['columns']:
                for i, value in enumerate(metrics['columns'][column]):
                    _run.log_scalar(column, value)

        # Attach artifacts during the run so observers capture them
        try:
            for artifact in artifacts:
                src = artifact.get('source_path') if isinstance(artifact, dict) else str(artifact)
                name = artifact.get('new_name') if isinstance(artifact, dict) else None
                if not src:
                    continue
                if not os.path.isabs(src):
                    src = os.path.join(experiment_folder or "", src)
                if os.path.exists(src):
                    _run.add_artifact(src, name=name)
        except Exception:
            pass
    ex.add_config(config)

    try:
        current_run = ex.run()
        return {
            "ok": True,
            "message": f"Experiment '{experiment_name or 'TEST_EXPERIMENT'}', run {current_run._id} sent successfully",
        }
    except Exception as e:
        import traceback
        print("ERROR running experiment:", e)
        print(traceback.format_exc())
        return {
            "ok": False,
            "message": f"Run failed: {e.__class__.__name__}: {e}",
        }
  
  


# mongo = payload.get("mongo", {}) or {}
# minio = payload.get("minio", {}) or {}
# experiment = payload.get("experiment", {}) or {}
# selectors = experiment.get("selectors", {}) or {}

# required_mongo = ["use_uri", "uri", "host", "port", "user", "db", "tls"]
# required_minio = ["endpoint", "access_key", "tls"]
# required_exp = ["folder"]
# required_selectors = ["config", "metrics", "results", "raw_data", "artifacts"]

# missing = []
# missing += [f"mongo.{k}" for k in required_mongo if k not in mongo]
# missing += [f"minio.{k}" for k in required_minio if k not in minio]
# missing += [f"experiment.{k}" for k in required_exp if k not in experiment]
# missing += [f"experiment.selectors.{k}" for k in required_selectors if k not in selectors]
# if missing:
#     return {"ok": False, "message": f"Missing required fields: {', '.join(missing)}"}

# message = {
#     "ok": True,
#     "message": "Experiment sent (stub)",
#     "summary": {
#         "mongo": {
#             "use_uri": bool(mongo.get("use_uri")),
#             "host": mongo.get("host"),
#             "db": mongo.get("db"),
#             "tls": bool(mongo.get("tls")),
#         },
#         "minio": {
#             "endpoint": minio.get("endpoint"),
#             "access_key": minio.get("access_key"),
#             "tls": bool(minio.get("tls")),
#         },
#         "experiment": {
#             "folder": experiment.get("folder"),
#             "selectors": selectors,
#         },
#     },
# }
# print(message)
# return message