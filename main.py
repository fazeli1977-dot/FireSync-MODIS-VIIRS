"""FireSync-MODIS-VIIRS  --  entry point."""
from __future__ import annotations
import os
import sys
from dotenv import load_dotenv
from src.ingest import download_firms
from src.harmonize import load_firms_csv, harmonize
from src.visualize import make_fire_map
from src.utils import get_logger

load_dotenv()
logger = get_logger("firesync")


def main() -> None:
    api_key = os.getenv("FIRMS_API_KEY", "").strip()
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        logger.error("FIRMS_API_KEY is not configured in your environment or .env file.")
        logger.info("Please get a free key at: https://firms.modaps.eosdis.nasa.gov/api/map_key/")
        logger.info("Then create a .env file with: FIRMS_API_KEY=your_key_here")
        sys.exit(1)

    # Example bounding box: Western United States
    bbox = dict(west=-125.0, south=32.0, east=-114.0, north=49.0)

    logger.info("=== FireSync-MODIS-VIIRS starting ===")

    modis_path = download_firms("MODIS_NRT", api_key, **bbox, day_range=7)
    viirs_path = download_firms("VIIRS_SNPP_NRT", api_key, **bbox, day_range=7)

    modis_gdf = load_firms_csv(modis_path)
    viirs_gdf = load_firms_csv(viirs_path)

    harmonized = harmonize(modis_gdf, viirs_gdf)
    map_path = make_fire_map(harmonized)

    logger.info("Done. Open %s in a browser to view the map.", map_path)


if __name__ == "__main__":
    main()