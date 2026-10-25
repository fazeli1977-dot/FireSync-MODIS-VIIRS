"""Download and load MODIS / VIIRS active-fire data from NASA FIRMS."""
from __future__ import annotations
import requests
from pathlib import Path
from io import StringIO
from urllib.parse import quote
import math
import pandas as pd
from src.utils import DATA_RAW, get_logger

logger = get_logger(__name__)

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

def download_firms(
    source: str,
    map_key: str,
    west: float,
    south: float,
    east: float,
    north: float,
    day_range: int = 5,
) -> Path:
    """Download active-fire CSV from NASA FIRMS and save to data/raw/.

    Args:
        source:    'MODIS_NRT' or 'VIIRS_SNPP_NRT' or 'VIIRS_NOAA20_NRT'
        map_key:   NASA FIRMS API key (https://firms.modaps.eosdis.nasa.gov/api/map_key/)
        west/south/east/north: bounding box in decimal degrees
        day_range: 1-5 days per Area API request

    Returns:
        Path to the saved CSV file.
    """
    if source not in {"MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"}:
        raise ValueError("Unsupported FIRMS source")
    if isinstance(day_range, bool) or not isinstance(day_range, int) or not 1 <= day_range <= 5:
        raise ValueError("day_range must be an integer from 1 to 5")
    if not map_key.strip():
        raise ValueError("A FIRMS map key is required")
    if not all(math.isfinite(x) for x in (west, south, east, north)) or not (
        -180 <= west < east <= 180 and -90 <= south < north <= 90
    ):
        raise ValueError("Invalid geographic bounding box")
    bbox = f"{west},{south},{east},{north}"
    url = f"{FIRMS_BASE}/{quote(map_key.strip(), safe='')}/{source}/{bbox}/{day_range}"
    logger.info("Fetching %s  bbox=%s  days=%d", source, bbox, day_range)
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.RequestException:
        # The request URL embeds the private key; keep it out of error output.
        raise RuntimeError("FIRMS request failed; check connectivity, key and service status") from None
    try:
        header = pd.read_csv(StringIO(resp.text), nrows=0)
    except (pd.errors.ParserError, pd.errors.EmptyDataError):
        raise ValueError("FIRMS response is not a detection CSV") from None
    if not {"latitude", "longitude", "acq_date", "acq_time", "frp", "confidence"}.issubset(header.columns):
        raise ValueError("FIRMS response is missing required detection columns")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / f"{source}_{day_range}d.csv"
    out.write_text(resp.text, encoding="utf-8")
    logger.info("Saved -> %s", out)
    return out
