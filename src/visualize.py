"""Map and chart utilities for FireSync-MODIS-VIIRS."""
from __future__ import annotations
import folium
import geopandas as gpd
from html import escape
from src.utils import DATA_PROCESSED, get_logger

logger = get_logger(__name__)


def make_fire_map(
    gdf: gpd.GeoDataFrame,
    title: str = "FireSync: Harmonized Hot Spots",
    out_name: str = "fire_map.html",
) -> str:
    """Render an interactive Folium map of hot-spot detections.

    Args:
        gdf:      GeoDataFrame with geometry (Point), frp_unified, source columns.
        title:    Map title shown in a top-left control.
        out_name: Output filename saved to data/processed/.

    Returns:
        Absolute path to the saved HTML file.
    """
    center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()] if not gdf.empty else [0.0, 0.0]
    m = folium.Map(location=center, zoom_start=6, tiles="OpenStreetMap")
    folium.map.Marker(
        [center[0] + 0.01, center[1]],
        icon=folium.DivIcon(html=f"<div style='font-size:14px;color:white'><b>{escape(title)}</b></div>"),
    ).add_to(m)

    color_map = {"BOTH": "#ff6a00", "MODIS": "#4fc3f7", "VIIRS": "#aed581"}

    for _, row in gdf.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=max(3, float(row.get("frp_unified", 3)) / 10),
            color=color_map.get(str(row.get("source", "BOTH")), "#ff6a00"),
            fill=True,
            fill_opacity=0.75,
            tooltip=(
                f"FRP: {row.get('frp_unified', 'N/A'):.1f} MW<br>"
                f"Source: {row.get('source', 'N/A')}<br>"
                f"Time: {row.get('acq_datetime', 'N/A')}"
            ),
        ).add_to(m)

    out = DATA_PROCESSED / out_name
    out.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out))
    logger.info("Map saved -> %s", out)
    return str(out)
