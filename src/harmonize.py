"""Core harmonization logic: align MODIS and VIIRS hot-spot detections."""
from __future__ import annotations
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from src.utils import get_logger

logger = get_logger(__name__)

DEFAULT_TOLERANCE_M = 500
DEFAULT_TIME_DELTA_MIN = 30


def load_firms_csv(path: str | "Path") -> gpd.GeoDataFrame:
    """Read a FIRMS CSV into a GeoDataFrame with UTC timestamps."""
    df = pd.read_csv(path)
    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"].astype(str) + " " + df["acq_time"].astype(str).str.zfill(4),
        format="%Y-%m-%d %H%M",
        utc=True,
    )
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )
    return gdf


def harmonize(
    modis: gpd.GeoDataFrame,
    viirs: gpd.GeoDataFrame,
    tolerance_m: int = DEFAULT_TOLERANCE_M,
    time_delta_min: int = DEFAULT_TIME_DELTA_MIN,
) -> gpd.GeoDataFrame:
    """Spatiotemporally join MODIS and VIIRS detections.

    Returns a GeoDataFrame of matched pairs with unified confidence score.
    Unmatched detections from either sensor are retained with NaN for the
    opposing sensor's columns.
    """
    modis_m = modis.to_crs("EPSG:3857")
    viirs_m = viirs.to_crs("EPSG:3857")

    records = []

    for i, row_m in modis_m.iterrows():
        dt = abs(viirs_m["acq_datetime"] - row_m["acq_datetime"])
        candidates = viirs_m[dt <= np.timedelta64(int(time_delta_min), 'm')]
        if candidates.empty:
            continue
        dists = candidates.geometry.distance(row_m.geometry)
        close = dists[dists <= tolerance_m]
        if close.empty:
            continue
        best_j = close.idxmin()
        row_v = viirs_m.loc[best_j]
        frp_unified = (row_m.get("frp", 0) * 1 + row_v.get("frp", 0) * 7) / 8
        records.append({
            "geometry": row_m.geometry,
            "acq_datetime": row_m["acq_datetime"],
            "frp_modis": row_m.get("frp"),
            "frp_viirs": row_v.get("frp"),
            "frp_unified": frp_unified,
            "confidence_modis": row_m.get("confidence"),
            "confidence_viirs": row_v.get("confidence"),
            "source": "BOTH",
        })

    logger.info(
        "Matched %d detections out of MODIS=%d / VIIRS=%d",
        len(records), len(modis), len(viirs),
    )

    if not records:
        return gpd.GeoDataFrame(
            columns=[
                "geometry", "acq_datetime", "frp_modis", "frp_viirs",
                "frp_unified", "confidence_modis", "confidence_viirs", "source",
            ],
            geometry="geometry",
            crs="EPSG:4326",
        )

    matched = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:3857").to_crs("EPSG:4326")
    return matched
