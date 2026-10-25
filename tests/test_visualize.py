from pathlib import Path
import json
import re
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from src import visualize
from src.harmonize import harmonize


def test_map_creates_output_directory_and_handles_empty_data(tmp_path, monkeypatch):
    monkeypatch.setattr(visualize, "DATA_PROCESSED", tmp_path / "processed")
    sample = gpd.GeoDataFrame([{
        "geometry": Point(-118, 34), "frp": 80,
        "acq_datetime": pd.Timestamp("2025-08-01", tz="UTC"), "confidence": 90,
    }], crs="EPSG:4326")
    for frame in (harmonize(sample, sample), harmonize(sample.iloc[:0], sample.iloc[:0])):
        path = Path(visualize.make_fire_map(frame, title="<Synthetic example>"))
        content = path.read_text(encoding="utf-8")
        assert "leaflet" in content.lower()
        title_json = re.search(r'"html": (".*?")', content).group(1)
        assert "&lt;Synthetic example&gt;" in json.loads(title_json)
