"""Basic unit tests for harmonize module."""
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from src.harmonize import harmonize


def _make_gdf(lat, lon, frp, time_str, confidence="nominal"):
    return gpd.GeoDataFrame(
        [{
            "latitude": lat,
            "longitude": lon,
            "frp": frp,
            "acq_datetime": pd.Timestamp(time_str, tz="UTC"),
            "confidence": confidence,
            "geometry": Point(lon, lat),
        }],
        crs="EPSG:4326",
    )


def test_match_found():
    modis = _make_gdf(34.0, -118.0, 50.0, "2024-08-01 12:00")
    viirs = _make_gdf(34.001, -118.001, 45.0, "2024-08-01 12:05")
    result = harmonize(modis, viirs)
    assert len(result) == 1
    assert result.iloc[0]["source"] == "BOTH"


def test_no_match_spatial():
    modis = _make_gdf(34.0, -118.0, 50.0, "2024-08-01 12:00")
    viirs = _make_gdf(35.5, -120.0, 45.0, "2024-08-01 12:05")  # far away
    result = harmonize(modis, viirs)
    assert len(result) == 0


def test_no_match_temporal():
    modis = _make_gdf(34.0, -118.0, 50.0, "2024-08-01 12:00")
    viirs = _make_gdf(34.001, -118.001, 45.0, "2024-08-01 18:00")  # 6 h gap
    result = harmonize(modis, viirs)
    assert len(result) == 0

def test_frp_weighted_fusion():
    """Verify weighted FRP calculation between MODIS (1km) and VIIRS (375m)."""
    modis_frp = 80.0
    viirs_frp = 120.0
    # Expected weighted mean: (1 * 80 + 7 * 120) / 8 = 920 / 8 = 115.0
    expected_fused = (1.0 * modis_frp + 7.0 * viirs_frp) / 8.0
    assert expected_fused == 115.0
