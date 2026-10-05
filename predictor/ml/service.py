"""Safe application boundary around a locally trusted serialized pipeline."""

import hashlib
import json
import math
from decimal import Decimal
from functools import lru_cache

import joblib
import pandas as pd
import sklearn
from django.conf import settings

from .features import FEATURES


class PredictionUnavailable(Exception):
    """A user-safe failure; technical details are logged by the caller."""


def model_metadata():
    try:
        metadata = json.loads(settings.MODEL_METADATA_PATH.read_text(encoding="utf-8"))
        if metadata["schema_version"] != 1 or metadata["features"] != FEATURES:
            return {}
        return metadata
    except (OSError, ValueError, KeyError, TypeError):
        return {}


@lru_cache(maxsize=1)
def _load_model(path, modified, expected_hash):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise PredictionUnavailable("The model artifact could not be verified.")
    # Only deserialize an artifact produced by this repository's training command.
    return joblib.load(path)


def estimate_price(features):
    try:
        metadata = model_metadata()
        if not metadata or not settings.MODEL_PATH.exists():
            raise PredictionUnavailable(
                "The prediction model is unavailable. Please try again later."
            )
        if metadata["versions"]["scikit_learn"] != sklearn.__version__:
            raise PredictionUnavailable("The model needs retraining for this environment.")
        pipeline = _load_model(
            settings.MODEL_PATH, settings.MODEL_PATH.stat().st_mtime_ns, metadata["model_sha256"]
        )
        frame = pd.DataFrame([{name: features[name] for name in FEATURES}], columns=FEATURES)
        price = float(pipeline.predict(frame)[0])
        if not math.isfinite(price) or price <= 0:
            raise PredictionUnavailable(
                "This property could not be estimated. Please review its details."
            )
        return Decimal(str(price)).quantize(Decimal("0.01")), metadata["selected_model"]
    except PredictionUnavailable:
        raise
    except Exception as error:
        raise PredictionUnavailable(
            "We couldn't calculate an estimate. Please try again later."
        ) from error
