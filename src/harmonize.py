"""Prototype one-to-one matching of MODIS and VIIRS point detections."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Geod

DEFAULT_TOLERANCE_M = 500
DEFAULT_TIME_DELTA_MIN = 30
GEOD = Geod(ellps="WGS84")
OUTPUT_COLUMNS = [
    "geometry", "acq_datetime", "frp_modis", "frp_viirs", "frp_unified",
    "confidence_modis", "confidence_viirs", "source",
]


def load_firms_csv(path: str | Path) -> gpd.GeoDataFrame:
    """Load FIRMS point CSV and reject malformed coordinates, times or FRP."""
    df = pd.read_csv(path, dtype={"acq_time": "string"})
    required = {"latitude", "longitude", "acq_date", "acq_time", "frp", "confidence"}
    if missing := required.difference(df.columns):
        raise ValueError(f"Missing FIRMS columns: {', '.join(sorted(missing))}")
    for column in ("latitude", "longitude", "frp"):
        df[column] = pd.to_numeric(df[column], errors="raise")
    if not np.isfinite(df[["latitude", "longitude", "frp"]].to_numpy()).all():
        raise ValueError("FIRMS coordinates and FRP must be finite")
    if not (df.latitude.between(-90, 90) & df.longitude.between(-180, 180)).all():
        raise ValueError("FIRMS coordinates outside geographic bounds")
    if (df.frp < 0).any():
        raise ValueError("FRP must be nonnegative")
    df["acq_datetime"] = pd.to_datetime(
        df["acq_date"].astype(str) + " " + df["acq_time"].str.zfill(4),
        format="%Y-%m-%d %H%M", utc=True, errors="raise",
    )
    if df.acq_datetime.isna().any():
        raise ValueError("Missing acquisition timestamp")
    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326",
    )


def harmonize(
    modis: gpd.GeoDataFrame,
    viirs: gpd.GeoDataFrame,
    tolerance_m: int = DEFAULT_TOLERANCE_M,
    time_delta_min: int = DEFAULT_TIME_DELTA_MIN,
) -> gpd.GeoDataFrame:
    """Greedily pair nearest eligible detections; preserve unmatched points.

    Eligible pairs have WGS84 geodesic distance <= tolerance_m and UTC time
    difference <= time_delta_min. Pairs are sorted by distance, time difference
    and input row position; each observation is used at most once. This is a
    deterministic heuristic, not an optimal assignment or a fire perimeter.
    Matched FRP uses the original experimental fixed weights MODIS:VIIRS=1:7;
    these weights are not confidence scores or a validated calibration.
    Matched location/time use MODIS. Unmatched FRP is kept unchanged.
    """
    if not np.isfinite([tolerance_m, time_delta_min]).all() or min(tolerance_m, time_delta_min) < 0:
        raise ValueError("Matching thresholds must be finite and nonnegative")
    frames = []
    for frame in (modis, viirs):
        frame = frame.to_crs("EPSG:4326").reset_index(drop=True).copy()
        frame["acq_datetime"] = pd.to_datetime(frame["acq_datetime"], utc=True)
        frame["frp"] = pd.to_numeric(frame["frp"], errors="raise")
        if frame.acq_datetime.isna().any() or frame.geometry.is_empty.any() or frame.geometry.isna().any():
            raise ValueError("Each detection needs a timestamp and point geometry")
        if not frame.geom_type.eq("Point").all():
            raise ValueError("Detections must be point geometries")
        if not np.isfinite(frame.frp).all() or (frame.frp < 0).any():
            raise ValueError("FRP must be finite and nonnegative")
        if not (frame.geometry.y.between(-90, 90) & frame.geometry.x.between(-180, 180)).all():
            raise ValueError("Detection coordinates outside geographic bounds")
        frames.append(frame)
    modis, viirs = frames
    candidates = []
    for i, row_m in modis.iterrows():
        delta = abs(viirs.acq_datetime - row_m.acq_datetime)
        for j, row_v in viirs[delta <= pd.Timedelta(minutes=time_delta_min)].iterrows():
            distance = GEOD.inv(row_m.geometry.x, row_m.geometry.y,
                                row_v.geometry.x, row_v.geometry.y)[2]
            if distance <= tolerance_m:
                candidates.append((distance, delta.loc[j].total_seconds(), i, j))

    records, used_m, used_v = [], set(), set()

    def record(row_m=None, row_v=None):
        anchor = row_m if row_m is not None else row_v
        fm = row_m.frp if row_m is not None else np.nan
        fv = row_v.frp if row_v is not None else np.nan
        both = row_m is not None and row_v is not None
        return {
            "geometry": anchor.geometry, "acq_datetime": anchor.acq_datetime,
            "frp_modis": fm, "frp_viirs": fv,
            "frp_unified": (fm + 7 * fv) / 8 if both else anchor.frp,
            "confidence_modis": row_m.get("confidence") if row_m is not None else None,
            "confidence_viirs": row_v.get("confidence") if row_v is not None else None,
            "source": "BOTH" if both else ("MODIS" if row_m is not None else "VIIRS"),
        }

    for _, _, i, j in sorted(candidates):
        if i not in used_m and j not in used_v:
            records.append(record(modis.iloc[i], viirs.iloc[j]))
            used_m.add(i)
            used_v.add(j)
    records.extend(record(row_m=row) for i, row in modis.iterrows() if i not in used_m)
    records.extend(record(row_v=row) for j, row in viirs.iterrows() if j not in used_v)
    return gpd.GeoDataFrame(records, columns=OUTPUT_COLUMNS, geometry="geometry", crs="EPSG:4326")
