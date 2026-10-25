"""Basic unit tests for harmonize module."""
import pandas as pd
import geopandas as gpd
import pytest
from pyproj import Geod
from shapely.geometry import Point
from src.harmonize import harmonize, load_firms_csv


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
    assert len(result) == 2
    assert set(result.source) == {"MODIS", "VIIRS"}


def test_no_match_temporal():
    modis = _make_gdf(34.0, -118.0, 50.0, "2024-08-01 12:00")
    viirs = _make_gdf(34.001, -118.001, 45.0, "2024-08-01 18:00")  # 6 h gap
    result = harmonize(modis, viirs)
    assert len(result) == 2
    assert set(result.source) == {"MODIS", "VIIRS"}

def test_frp_weighted_fusion():
    """Verify weighted FRP calculation between MODIS (1km) and VIIRS (375m)."""
    modis_frp = 80.0
    viirs_frp = 120.0
    modis = _make_gdf(34, -118, modis_frp, "2025-08-01 12:00")
    viirs = _make_gdf(34, -118, viirs_frp, "2025-08-01 12:05")
    assert harmonize(modis, viirs).iloc[0].frp_unified == pytest.approx(115.0)


def test_viirs_observation_is_not_reused():
    first = _make_gdf(34, -118, 80, "2025-08-01 12:00")
    second = _make_gdf(34.001, -118, 40, "2025-08-01 12:00")
    # Duplicate input labels must not interfere with one-to-one matching.
    modis = pd.concat([first, second])
    viirs = _make_gdf(34, -118, 120, "2025-08-01 12:05")
    result = harmonize(modis, viirs)
    assert list(result.source) == ["BOTH", "MODIS"]
    assert result.iloc[1].frp_unified == 40


def test_empty_and_single_sensor_inputs():
    modis = _make_gdf(34, -118, 80, "2025-08-01 12:00")
    empty = modis.iloc[:0]
    assert harmonize(empty, empty).empty
    assert harmonize(empty, modis).iloc[0].source == "VIIRS"
    assert harmonize(modis, empty).iloc[0].source == "MODIS"


@pytest.mark.parametrize("distance, matched", [(499, True), (501, False)])
def test_ground_distance_at_high_latitude(distance, matched):
    lon, lat, _ = Geod(ellps="WGS84").fwd(10, 70, 90, distance)
    modis = _make_gdf(70, 10, 80, "2025-08-01 12:00")
    viirs = _make_gdf(lat, lon, 120, "2025-08-01 12:30")
    result = harmonize(modis, viirs)
    assert (result.source == "BOTH").any() == matched


def test_csv_timestamp_padding_and_validation(tmp_path):
    path = tmp_path / "detections.csv"
    path.write_text("latitude,longitude,acq_date,acq_time,frp,confidence\n34,-118,2025-08-01,5,80,90\n")
    loaded = load_firms_csv(path)
    assert loaded.iloc[0].acq_datetime == pd.Timestamp("2025-08-01 00:05", tz="UTC")
    path.write_text("latitude,longitude,acq_date,acq_time,frp,confidence\n91,-118,2025-08-01,5,80,90\n")
    with pytest.raises(ValueError, match="bounds"):
        load_firms_csv(path)


def test_invalid_thresholds_and_negative_frp():
    sample = _make_gdf(34, -118, 80, "2025-08-01 12:00")
    with pytest.raises(ValueError, match="thresholds"):
        harmonize(sample, sample, tolerance_m=-1)
    sample["frp"] = -1
    with pytest.raises(ValueError, match="FRP"):
        harmonize(sample, sample)
