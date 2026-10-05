"""Strict dataset validation and estimator-owned preprocessing."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import CATEGORY_VALUES, CATEGORICAL_FEATURES, FEATURES, NUMERIC_LIMITS


def load_dataset(path):
    frame = pd.read_csv(path)
    missing = set(FEATURES + ["price"]) - set(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    original_rows = len(frame)
    frame = frame[FEATURES + ["price"]].copy().drop_duplicates()
    for name, values in CATEGORY_VALUES.items():
        frame[name] = frame[name].astype("string").str.strip()
        frame = frame[frame[name].isin(values)]
    for name, (low, high) in NUMERIC_LIMITS.items():
        frame[name] = pd.to_numeric(frame[name], errors="coerce")
        frame = frame[frame[name].between(low, high)]
        if name != "distance_city_center":
            frame = frame[frame[name] % 1 == 0]
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame = frame[np.isfinite(frame["price"]) & (frame["price"] > 0)]
    frame = frame[frame.area_sqft >= 120 * (frame.bedrooms + frame.bathrooms)]
    frame = frame[(frame.property_type != "Apartment") | (frame.floors == 1)]
    if len(frame) < 500:
        raise ValueError("At least 500 valid, unique rows are required for training.")
    return frame.reset_index(drop=True), original_rows - len(frame)


def build_preprocessor():
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, list(NUMERIC_LIMITS)),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )
