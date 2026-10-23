from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.express as px
from data.sample_data import get_harmonized_sample

# -- Page config --------------------------------------------------------------
st.set_page_config(
    page_title="FireSync – MODIS & VIIRS Harmonization",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Theme tokens (injected via st.markdown) -----------------------------------
st.markdown("""
<style>
:root {
    --bg:        oklch(14% 0.01 250);
    --surface:   oklch(19% 0.012 250);
    --border:    oklch(28% 0.015 250);
    --muted:     oklch(55% 0.01 250);
    --body:      oklch(88% 0.008 250);
    --accent:    oklch(68% 0.18 38);   /* warm orange */
    --accent-lo: oklch(30% 0.10 38);
}
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
    color: var(--body);
}
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
h1, h2, h3 { color: var(--accent); font-weight: 700; letter-spacing: -0.02em; }
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem 1rem;
}
</style>
""", unsafe_allow_html=True)

# -- Load data -----------------------------------------------------------------
@st.cache_data
def load_data():
    return get_harmonized_sample(300)

df = load_data()

# -- Sidebar -------------------------------------------------------------------
st.sidebar.title("🔥 FireSync Controls")
st.sidebar.markdown("---")

instruments = st.sidebar.multiselect(
    "Instrument",
    options=df["instrument"].unique().tolist(),
    default=df["instrument"].unique().tolist(),
)

date_min = df["acq_date"].min().date()
date_max = df["acq_date"].max().date()
date_input_val = st.sidebar.date_input(
    "Acquisition date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

if isinstance(date_input_val, (tuple, list)) and len(date_input_val) == 2:
    start_date, end_date = date_input_val
elif isinstance(date_input_val, (tuple, list)) and len(date_input_val) == 1:
    start_date = end_date = date_input_val[0]
else:
    start_date, end_date = date_min, date_max

frp_range = st.sidebar.slider(
    "FRP range (MW)",
    min_value=float(df["frp"].min()),
    max_value=float(df["frp"].max()),
    value=(float(df["frp"].min()), float(df["frp"].max())),
)

# -- Filter --------------------------------------------------------------------
mask = (
    df["instrument"].isin(instruments)
    & (df["acq_date"].dt.date >= start_date)
    & (df["acq_date"].dt.date <= end_date)
    & (df["frp"] >= frp_range[0])
    & (df["frp"] <= frp_range[1])
)
filtered = df[mask].copy()

# -- Header --------------------------------------------------------------------
st.title("FireSync — MODIS & VIIRS Hot-Spot Harmonization")
st.caption("NASA Space Apps Challenge 2026 · Team ClimateLens Engine · Sample demo data")
st.markdown("---")

# -- KPI row ------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total detections", f"{len(filtered):,}")
k2.metric("MODIS detections", f"{len(filtered[filtered.instrument=='MODIS']):,}")
k3.metric("VIIRS detections", f"{len(filtered[filtered.instrument=='VIIRS']):,}")
mean_frp = filtered['frp'].mean() if len(filtered) > 0 else 0.0
k4.metric("Mean FRP (MW)", f"{mean_frp:.1f}")

st.markdown("---")

# -- Map ----------------------------------------------------------------------
st.subheader("Geospatial Distribution")
fig_map = px.scatter_map(
    filtered,
    lat="latitude",
    lon="longitude",
    color="instrument",
    size="frp" if len(filtered) > 0 else None,
    size_max=18,
    color_discrete_map={"MODIS": "#f97316", "VIIRS": "#38bdf8"},
    hover_data={"frp": ":.1f", "brightness": ":.1f", "confidence": True, "acq_date": True} if len(filtered) > 0 else None,
    map_style="carto-darkmatter",
    zoom=3,
    center={"lat": 40.5, "lon": -114.5},
    height=480,
)
fig_map.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=0, b=0),
    legend=dict(font_color="#e2e8f0"),
)
st.plotly_chart(fig_map, width='stretch')

# -- Two-column charts ---------------------------------------------------------
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("FRP Distribution by Instrument")
    fig_box = px.box(
        filtered,
        x="instrument",
        y="frp",
        color="instrument",
        color_discrete_map={"MODIS": "#f97316", "VIIRS": "#38bdf8"},
        labels={"frp": "Fire Radiative Power (MW)"},
    )
    fig_box.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        yaxis=dict(gridcolor="#2d3748"),
        xaxis=dict(gridcolor="#2d3748"),
        font_color="#cbd5e1",
    )
    st.plotly_chart(fig_box, width='stretch')

with col_r:
    st.subheader("Daily Detection Count")
    daily = (
        filtered.groupby(["acq_date", "instrument"])
        .size()
        .reset_index(name="count")
    )
    fig_line = px.line(
        daily,
        x="acq_date",
        y="count",
        color="instrument",
        color_discrete_map={"MODIS": "#f97316", "VIIRS": "#38bdf8"},
        labels={"acq_date": "Date", "count": "Detections"},
    )
    fig_line.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#2d3748"),
        xaxis=dict(gridcolor="#2d3748"),
        font_color="#cbd5e1",
        legend=dict(font_color="#cbd5e1"),
    )
    st.plotly_chart(fig_line, width='stretch')

# -- Confidence vs FRP scatter -------------------------------------------------
st.subheader("Confidence vs Fire Radiative Power")
fig_sc = px.scatter(
    filtered,
    x="confidence",
    y="frp",
    color="instrument",
    color_discrete_map={"MODIS": "#f97316", "VIIRS": "#38bdf8"},
    opacity=0.7,
    trendline="ols" if len(filtered) > 1 else None,
    labels={"confidence": "Confidence Score", "frp": "FRP (MW)"},
    height=360,
)
fig_sc.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(gridcolor="#2d3748"),
    xaxis=dict(gridcolor="#2d3748"),
    font_color="#cbd5e1",
    legend=dict(font_color="#cbd5e1"),
)
st.plotly_chart(fig_sc, width='stretch')

# -- Raw data table -----------------------------------------------------------
with st.expander("View raw harmonized data"):
    st.dataframe(
        filtered.reset_index(drop=True),
        width='stretch',
        height=320,
    )

st.markdown("---")
st.caption("Data shown is synthetic sample data generated for demonstration purposes only.")

