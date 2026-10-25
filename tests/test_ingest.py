from types import SimpleNamespace
import pytest
import requests
from src import ingest

CSV = "latitude,longitude,acq_date,acq_time,frp,confidence\n34,-118,2025-08-01,1200,80,90\n"
BBOX = dict(west=-125, south=32, east=-114, north=49)


def test_download_creates_directory_and_uses_supported_range(tmp_path, monkeypatch):
    calls = []
    def fake_get(url, timeout):
        calls.append((url, timeout))
        return SimpleNamespace(text=CSV, raise_for_status=lambda: None)
    monkeypatch.setattr(ingest.requests, "get", fake_get)
    monkeypatch.setattr(ingest, "DATA_RAW", tmp_path / "new" / "raw")
    path = ingest.download_firms("MODIS_NRT", "fake-test-key", **BBOX)
    assert path.read_text() == CSV
    assert calls[0][0].endswith("/MODIS_NRT/-125,32,-114,49/5")


def test_rejects_service_error_before_saving(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest.requests, "get", lambda *a, **kw:
                        SimpleNamespace(text="Invalid MAP_KEY", raise_for_status=lambda: None))
    monkeypatch.setattr(ingest, "DATA_RAW", tmp_path / "raw")
    with pytest.raises(ValueError, match="required detection columns"):
        ingest.download_firms("MODIS_NRT", "fake-test-key", **BBOX)
    assert not (tmp_path / "raw").exists()


@pytest.mark.parametrize("days", [0, 6, 7, True])
def test_invalid_day_range_is_rejected_without_request(days):
    with pytest.raises(ValueError, match="day_range"):
        ingest.download_firms("MODIS_NRT", "fake-test-key", **BBOX, day_range=days)


def test_network_error_does_not_expose_map_key(monkeypatch):
    def fail(*a, **kw):
        raise requests.ConnectionError("URL contains private-test-key")
    monkeypatch.setattr(ingest.requests, "get", fail)
    with pytest.raises(RuntimeError) as error:
        ingest.download_firms("MODIS_NRT", "private-test-key", **BBOX)
    assert "private-test-key" not in str(error.value)
