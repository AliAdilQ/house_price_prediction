"""Choose with cross-validation; evaluate the winner on an untouched test set."""

import hashlib
import json
import os
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline

from .features import FEATURES
from .preprocessing import build_preprocessor, load_dataset


def train(dataset_path, model_path, metadata_path):
    frame, removed_rows = load_dataset(dataset_path)
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURES], frame.price, test_size=0.2, random_state=42
    )
    estimators = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=180, min_samples_leaf=2, random_state=42, n_jobs=1
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=300,
            learning_rate=0.06,
            max_depth=3,
            min_samples_leaf=5,
            loss="huber",
            random_state=42,
        ),
    }
    pipelines, comparison = {}, []
    cv = KFold(n_splits=3, shuffle=True, random_state=42)
    for name, estimator in estimators.items():
        pipeline = Pipeline([("preprocess", build_preprocessor()), ("regressor", estimator)])
        scores = cross_validate(
            pipeline,
            x_train,
            y_train,
            cv=cv,
            n_jobs=1,
            scoring={
                "r2": "r2",
                "mae": "neg_mean_absolute_error",
                "rmse": "neg_root_mean_squared_error",
            },
        )
        comparison.append(
            {
                "name": name,
                "r2": float(np.mean(scores["test_r2"])),
                "mae": float(-np.mean(scores["test_mae"])),
                "rmse": float(-np.mean(scores["test_rmse"])),
            }
        )
        pipelines[name] = pipeline
    winner = min(comparison, key=lambda item: item["rmse"])["name"]
    pipeline = pipelines[winner].fit(x_train, y_train)
    estimates = pipeline.predict(x_test)
    test_metrics = {
        "r2": float(r2_score(y_test, estimates)),
        "mae": float(mean_absolute_error(y_test, estimates)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, estimates))),
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = model_path.with_suffix(".joblib.tmp")
    joblib.dump(pipeline, temporary, compress=3)
    artifact_hash = hashlib.sha256(temporary.read_bytes()).hexdigest()
    metadata = {
        "schema_version": 1,
        "selected_model": winner,
        "currency": "USD",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "random_state": 42,
        "dataset_rows": len(frame),
        "removed_invalid_rows": removed_rows,
        "training_rows": len(x_train),
        "test_rows": len(x_test),
        "selection": "3-fold cross-validation RMSE on training split",
        "comparison": comparison,
        "test_metrics": test_metrics,
        "features": FEATURES,
        "versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "model_sha256": artifact_hash,
        "synthetic": True,
    }
    metadata_temp = metadata_path.with_suffix(".json.tmp")
    metadata_temp.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, model_path)
    os.replace(metadata_temp, metadata_path)
    return metadata
