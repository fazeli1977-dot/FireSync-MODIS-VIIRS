# FireSync - Portfolio Presentation

## 1. Purpose

A Python prototype for exploring active-fire and thermal-anomaly point detections from MODIS and VIIRS. This presentation makes no claim about competition participation or submission history.

## 2. The problem

Sensors observe at different times and nominal spatial resolutions. A configurable point-matching experiment can help inspect possible cross-sensor correspondences. It does not identify a fire perimeter or prove which detections describe the same fire.

## 3. Implemented processing

FIRMS CSV download code and UTC timestamp parsing feed a geodesic matching routine. Defaults are 500 m and 30 minutes. Eligible pairs are sorted by distance and greedily selected one-to-one; unmatched observations are retained. Matched locations/times use MODIS. Experimental fixed MODIS:VIIRS weights of 1:7 combine FRP, without confidence weighting or validated calibration.

## 4. Two separate demonstrations

The Streamlit dashboard generates synthetic detections locally for maps, FRP/date/instrument filters and charts. It does not display live NASA observations or matching results. The command-line pipeline can request MODIS_NRT and VIIRS_SNPP_NRT CSVs with a valid key and save a Folium map. A successful live run has not been recorded in this review.

## 5. Evidence and reproducibility

Source, install/run instructions and tests accompany the project. Tests cover functional edge cases and mocked downloads; actual results are recorded in validation.md. A localhost app is a local demonstration, not a public hosted service. No automatic CI success, operational deployment or measured impact is claimed.

## 6. Scientific limits and next evidence

NRT and nominal VIIRS 375 m resolution describe upstream products. They do not establish this application's latency or output accuracy. Record a real-data run, investigate matching/FRP methodology with independent reference cases, and evaluate performance before stronger claims. Fire-spread forecasting and automated spread alerts are unimplemented future ideas.

## 7. Sources and rights

NASA FIRMS: `https://firms.modaps.eosdis.nasa.gov/`

Area API: `https://firms.modaps.eosdis.nasa.gov/api/area/`

MODIS product context: `https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/index.html`

VIIRS 375 m product context: `https://modaps.modaps.eosdis.nasa.gov/services/about/products/viirs-land-c2-nrt/vj114imgtdl_nrt.html`

See README.md for details. The revised local code includes an MIT license, copyright (c) 2026 Alireza Sani, following the owner's explicit selection and attribution. This license does not cover NASA data or third-party dependencies.
