from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_synthetic_dashboard_starts_and_handles_empty_selection():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "300"
    assert any("Synthetic sample detections only" in message.value for message in app.info)
    app.multiselect[0].set_value([]).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "0"
    assert any("No sample detections" in message.value for message in app.info)
