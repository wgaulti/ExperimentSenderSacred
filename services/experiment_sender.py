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
from services.raw_data_saver import save_raw_data
from services.mongo_conn import build_mongo_url_from_payload


def send_experiment(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Validate presence of top-level domains
    if not isinstance(payload, dict):
        return {"ok": False, "message": "Invalid payload"}

    data_payload = payload.get("experiment", {}) or {}
    mongo_payload = payload.get("mongo", {}) or {}
    # experiment_name = (data_payload.get("name") or "").strip()
    selectors = data_payload.get("selectors", {}) or {}
    config = selectors.get("config", {}) or {}
    metrics = selectors.get("metrics", {}) or {}
    results = selectors.get("results", {}) or {}
    raw_data = selectors.get("raw_data", {}) or {}
    artifacts = selectors.get("artifacts", {}) or {}
    folders = data_payload.get("folders", [])

    raw_data_save_options = raw_data.get("options", {}) or {}

    # --- Build Mongo connection using shared helper ---
    mongo_payload = payload.get("mongo", {}) or {}
    mongo_url, mongo_db = build_mongo_url_from_payload(mongo_payload)

    print(f"payload: {payload}\n")
    # Attach Mongo observer

    # Keep originals for per-folder formatting
    base_config = config
    base_results = results
    base_raw_data = raw_data
    base_artifacts = artifacts
    base_metrics = metrics
    results_messages = []

    if folders and len(folders) > 0:
        all_ok = True
        for folder in folders:
            experiment_name = folder.replace("\\", "/").split("/")[-1]
            cfg = {'experiment': experiment_name}
            cfg.update(fc.format_config(folder, base_config))
            mets = fc.format_metrics(folder, base_metrics)
            arts = fc.format_raw_data(folder, base_artifacts)
            res = fc.format_results(folder, base_results)
            rawda = fc.format_raw_data(folder, base_raw_data)
            ex = Experiment(experiment_name, save_git_info=True)
            try:
                ex.observers.append(MongoObserver(url=mongo_url, db_name=mongo_db))
            except Exception:
                pass

            @ex.main
            def run(_run, _mets=mets, _arts=arts, _folder=folder, _res=res):
                print(f"res: {_res}\n")
                data_files = {}
                if isinstance(_mets, dict) and 'columns' in _mets:
                    if 'x_axis' in _mets:
                        x_axis = _mets['x_axis']
                        for column in _mets['columns']:
                            for i, value in enumerate(_mets['columns'][column]):
                                _run.log_scalar(column, value, step=x_axis[i])
                    else:
                        for column in _mets['columns']:
                            for i, value in enumerate(_mets['columns'][column]):
                                _run.log_scalar(column, value)
                try:
                    config_arts = {}
                    for a in _arts.values():
                        src = a.get('source_path') if isinstance(a, dict) else str(a)
                        name = a.get('new_name') if isinstance(a, dict) else None
                        if not src:
                            continue
                        if os.path.exists(src):
                            _run.add_artifact(src, name=name)
                            config_arts[a.get('minio_folder')] = name
                        data_files['artifacts'] = config_arts
                except Exception:
                    pass

                try:
                    if len(rawda) > 0:
                        rd_result, rd_config = save_raw_data(rawda, raw_data_save_options, payload.get("minio", {}) or {})
                        cfg['raw_data'] = rd_config
                        print(f"raw_data save: {rd_result}")
                        data_files['raw_data'] = rd_config

                except Exception as e:
                    print(f"ERROR saving raw_data: {e}")

                _run.info['dataFiles'] = data_files
                _run.info['result'] = _res
            

            ex.add_config(cfg)

            try:
                current_run = ex.run(options={'--capture': 'no'})
                current_run.result = res
                # After run, optionally save raw_data (if any) according to options
                results_messages.append(f"{experiment_name or 'TEST_EXPERIMENT'}, run {current_run._id} sent")
            except Exception as e:
                import traceback
                print("ERROR running experiment:", e)
                print(traceback.format_exc())
                all_ok = False
                results_messages.append(f"{experiment_name or 'TEST_EXPERIMENT'} failed: {e}")
        return {"ok": all_ok, "message": "; ".join(results_messages)}