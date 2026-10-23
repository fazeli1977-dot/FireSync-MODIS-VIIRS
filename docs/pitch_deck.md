# 🛰️ FireSync: MODIS & VIIRS Hot-Spot Harmonization
### NASA Space Apps Challenge 2026 — Pitch Deck
**Team Lead:** Alireza Sani ([@fazeli1977-dot](https://github.com/fazeli1977-dot))  
**Repository:** [FireSync-MODIS-VIIRS](https://github.com/fazeli1977-dot/FireSync-MODIS-VIIRS)  
**License:** MIT Open Source  

---

## Slide 1: Executive Summary & Vision
- **Project:** FireSync — Cross-Sensor Wildfire Intelligence Engine.
- **Goal:** Harmonize multi-platform Earth Observation streams (Aqua/Terra MODIS & Suomi-NPP/NOAA-20 VIIRS).
- **Core Outcome:** Real-time deduplication, spatial re-centering, and calibrated Fire Radiative Power (FRP) estimation.

---

## Slide 2: The Earth Observation Problem
- **Spatial Resolution Mismatch:** MODIS (1 km) vs. VIIRS (375 m) creates divergent fire front estimations.
- **Overpass Offset:** Orbit timing gaps produce asynchronous wildfire observations.
- **FRP Discrepancies:** Raw thermal outputs vary significantly under differing scan angles and cloud masks.
- **Operational Hazard:** Crisis responders receive duplicated alerts and fragmented operational pictures.

---

## Slide 3: Harmonization & Scientific Methodology
- **Spatio-Temporal Coincidence Window:**
  - Spatial threshold: $d \le 500\,\text{m}$
  - Temporal threshold: $\Delta t \le 30\,\text{minutes}$
- **Confidence Normalization:**
  - VIIRS levels (`low`, `nominal`, `high`) $\rightarrow$ $[0.3, 0.7, 1.0]$
  - MODIS percentages $\rightarrow [0.0 - 1.0]$
- **Weighted FRP Fusion Formula:**
  $$\text{FRP}_{\text{fused}} = \frac{w_m \cdot \text{FRP}_m + w_v \cdot \text{FRP}_v}{w_m + w_v}$$
- **Projection:** Dynamic planar UTM conversion using GeoPandas / EPSG:3857 for metric precision.

---

## Slide 4: System Architecture & Testing Rigor
- **NASA FIRMS Ingestion:** Robust API connector supporting Near Real-Time (NRT) satellite feeds.
- **Processing Core:** `src/harmonize.py` handles spatial join, deduplication, and confidence weighting.
- **Strict Quality Control:** 100% pytest suite pass rate (`4/4 passed`) across spatial, temporal, and FRP fusion tests.
- **Environment:** Python 3.12, GeoPandas, NumPy, Streamlit, Folium.

---

## Slide 5: Interactive Dashboard & Field Usability
- **Real-Time Visuals:** Folium-powered interactive map layers distinguishing raw vs. harmonized hot-spots.
- **Dynamic Threshold Controls:** Interactive sliders for spatial tolerance ($m$) and FRP cutoffs.
- **Decision Metrics:** Live metrics displaying total detections, deduplication rate, and aggregate thermal energy (MW).
- **Interoperability:** Instant export to GeoJSON and CSV for GIS emergency systems.

---

## Slide 6: Real-World Impact & Roadmap
- **Resource Dispatch:** Dramatically lowers false cluster alarms and redundant fire engine deployments.
- **Cross-Agency Readiness:** Formatted for easy ingestion by civil protection agencies worldwide.
- **Roadmap 2026+:**
  - Incorporating Landsat-Next thermal infrared data.
  - Integration with geostationary GOES-R and Meteosat high-frequency scans.
  - Physics-informed AI for active perimeter spread forecasting.

---

## Slide 7: Open Science & NASA Space Apps Artifacts
- **Source Code:** [https://github.com/fazeli1977-dot/FireSync-MODIS-VIIRS](https://github.com/fazeli1977-dot/FireSync-MODIS-VIIRS)
- **Primary Data Sources:** NASA FIRMS (MODIS C6.1 & VIIRS VNP14IMGTDL / VJ114IMGTDL).
- **Standards:** Open-source, reproducible, fully automated CI/test workflow.
