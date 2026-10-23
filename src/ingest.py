"""Download and load MODIS / VIIRS active-fire data from NASA FIRMS."""
from __future__ import annotations
import requests
from pathlib import Path
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
    day_range: int = 7,
) -> Path:
    """Download active-fire CSV from NASA FIRMS and save to data/raw/.

    Args:
        source:    'MODIS_NRT' or 'VIIRS_SNPP_NRT' or 'VIIRS_NOAA20_NRT'
        map_key:   NASA FIRMS API key (https://firms.modaps.eosdis.nasa.gov/api/map_key/)
        west/south/east/north: bounding box in decimal degrees
        day_range: 1-10 days of data

    Returns:
        Path to the saved CSV file.
    """
    bbox = f"{west},{south},{east},{north}"
    url = f"{FIRMS_BASE}/{map_key}/{source}/{bbox}/{day_range}"
    logger.info("Fetching %s  bbox=%s  days=%d", source, bbox, day_range)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    out = DATA_RAW / f"{source}_{day_range}d.csv"
    out.write_text(resp.text, encoding="utf-8")
    logger.info("Saved -> %s", out)
    return out
