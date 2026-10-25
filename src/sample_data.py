"""Deterministic synthetic detections for the offline portfolio dashboard.

No satellite data are downloaded here. These rows are not harmonize() output.
"""
import numpy as np
import pandas as pd


def get_sample_detections(count: int = 300) -> pd.DataFrame:
    """Return repeatable synthetic rows in a display-friendly schema."""
    if count < 1:
        raise ValueError("At least one sample detection is required")
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "latitude": rng.uniform(34, 47, count),
        "longitude": rng.uniform(-123, -116, count),
        "instrument": np.where(np.arange(count) % 2, "VIIRS", "MODIS"),
        "acq_date": pd.Timestamp("2025-08-01") + pd.to_timedelta(rng.integers(0, 5, count), unit="D"),
        "frp": rng.uniform(1, 150, count),
        "brightness": rng.uniform(300, 380, count),
        "confidence": rng.integers(30, 101, count),
    })
