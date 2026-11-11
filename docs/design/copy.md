# PyroScope Copy Deck & Content Standards

This document establishes the user-facing copy, terminology guidelines, plain-language scientific explanations, empty/error state messages, and legal/attribution disclaimers for **PyroScope**.

---

## 1. Terminology & Plain-Language Explanations

Accuracy and scientific honesty are non-negotiable. PyroScope translates satellite remote sensing physics into accessible language without losing rigor.

### 1.1 "Harmonized MODIS-Equivalent Fire Events"
- **Short Tooltip / Label**: *Harmonized Fire Events*
- **Plain-Language Summary (for UI cards & tooltips)**:
  > *"Because the VIIRS satellite sensor (375 m pixel resolution) detects four times more small hot spots than the older MODIS sensor (1 km resolution), uncorrected records falsely jump in 2012. PyroScope groups raw hot spots into physical fire events and calibrates VIIRS counts to the 26-year MODIS baseline using quantile mapping. The result is a single, uninterrupted fire activity index from 2000 to the present day."*
- **What it is NOT (Strict Prohibition)**:
  - Never call it "burned area", "hectares burned", or "number of wildfires".
  - Always state: *"Active-fire detections are thermal hot spots; harmonized numbers represent MODIS-equivalent fire events."*

### 1.2 "Anomaly Classes" (Normal, Elevated, Extreme)
- **Short Labels**: `Normal`, `Elevated`, `Extreme`
- **Plain-Language Summary**:
  > *"An anomaly measures whether burning in a specific month was unusual compared to historical history for that same calendar month over the past 25 years (using a leave-one-out baseline)."*
- **Class Definitions**:
  - **Normal (`●`)**: Activity is within the historical typical range ($\le 90\text{th}$ percentile of historical baseline).
  - **Elevated (`▲`)**: Activity exceeds $90\%$ of past years ($> 90\text{th}$ to $95\text{th}$ percentile). Early warning indicator.
  - **Extreme (`◆`)**: Activity exceeds $95\%$ of all historical observations ($> 95\text{th}$ percentile). Unprecedented or near-record fire conditions.

### 1.3 "Burning Season"
- **Short Label**: *Fire Season Window*
- **Plain-Language Summary**:
  > *"The shortest consecutive window of calendar months that historically accounts for at least 70% of an area's annual fire activity. For example, in the Chittagong Hill Tracts, over 97% of fire events occur strictly between March and May, peaking in April."*

### 1.4 "The Hidden Jump" (Diagnostic View)
- **Headline**: *The "Hidden Jump": Why Raw Satellite Data Misleads*
- **Explainer Copy**:
  > *"In 2012, NASA launched the VIIRS sensor alongside MODIS. Looking at raw fire counts makes it appear that fires quadrupled overnight. In reality, the fire activity did not change—the satellite's camera simply became sharper. Naively splicing raw data creates a false trend. PyroScope's harmonization restores historical consistency."*

---

## 2. Screen Titles & Section Headlines

| Screen / Feature | Primary Title (H1) | Subtitle / Explainer (H2/H3) |
| :--- | :--- | :--- |
| **Main Mission Control** | `PyroScope` | `NASA MODIS & VIIRS Harmonized Burning Activity Calendar (2000–Present)` |
| **Area Selector** | `Select Area of Interest` | `Choose a national preset, administrative division, district, or draw a bounding box.` |
| **Hex Map View** | `Active-Fire Spatial Density` | `H3 hexagonal resolution-7 grid showing harmonized fire event concentration.` |
| **FireCalendar Panel** | `FireCalendar` | `Monthly fire climatology, anomaly matrix, and seasonal recurrence bands.` |
| **The Hidden Jump** | `The Calibration Gap` | `Comparing Raw MODIS, Raw VIIRS, Naive Splice, and Harmonized Series (2000–2026).` |
| **Ask PyroScope** | `Ask PyroScope Assistant` | `Evidence-grounded satellite fire analysis powered by typed tools and data verification.` |
| **Methodology Page** | `Scientific Methodology & Transparency` | `Mathematical formulations, ST-DBSCAN clustering, quantile mapping, and error diagnostics.` |
| **Early Warning Alerts (P1)**| `Fire Season Notifications` | `Advisory alerts when an area's fire season approaches or anomalous burning begins.` |
| **Wildland Action Planner (P1)**| `Action Guidance` | `Seasonal preparedness and prevention checklists tailored to local fire regimes.` |

---

## 3. Navigation & Action Button Labels

- **Presets**: `Chittagong Hill Tracts (CHT)`, `Bangladesh (National)`, `Custom Bounding Box`
- **Metric Toggles**: `Harmonized (Calibrated)`, `Raw MODIS (1 km)`, `Raw VIIRS (375 m)`
- **Map Layer Controls**: `3D Hex Extrusion: On/Off`, `Resolution: R5 / R6 / R7`, `Basemap Style: Dark / Satellite`
- **Time Controls**: `Play Timeline`, `Pause`, `Speed: 1x / 2x`, `Reset Range (2000-2026)`
- **Assistant Actions**: `Ask Question`, `Replay Verified Answer`, `View Tool Calls`, `Copy Answer`, `Export Citations`
- **Data Export**: `Download Parquet`, `Download GeoJSON`, `Export CSV`, `View API Reference`

---

## 4. UI States: Loading, Empty, and Error States

### 4.1 Loading States
- **Map Layer Loading**: *"Assembling H3 hexagonal fire bins for {area_name} ({date_range})..."*
- **FireCalendar Loading**: *"Calculating 25-year monthly baseline and percentile ranks..."*
- **Assistant Streaming**: *"Querying PyroScope data engine..."* $\to$ *"Computing leave-one-out climatology..."* $\to$ *"Generating grounded response with citations..."*
- **API Health Check**: *"Connecting to DuckDB telemetry engine..."*

### 4.2 Empty States
- **No Fires in Area/Period**:
  - *Title*: `No Fire Events Recorded`
  - *Message*: *"No active-fire events met the confidence criteria in {area_name} during {period}. During the monsoon months (June–September), cloud cover and heavy rainfall suppress fire occurrences."*
  - *Action*: `Expand Date Range` or `Reset to Peak Season`
- **No Search Results in Area Selector**:
  - *Title*: `Area Not Found`
  - *Message*: *"No district or preset matches '{query}'. Check spelling or enter coordinates as 'bbox:minLon,minLat,maxLon,maxLat'."*
- **Assistant Tool Yields Zero Events**:
  - *Message*: *"Based on the processed satellite records for {area_name}, zero active-fire events were detected in {year}. This represents a historically quiet period."*

### 4.3 Error Messages
- **DuckDB Query Timeout / Validation**:
  - *Title*: `Data Query Failed`
  - *Message*: *"Unable to load fire density cells. Please verify that the selected bounding box is within supported coordinates (88.0°E–92.8°E, 20.5°N–26.7°N)."*
  - *Action*: `Retry Query`
- **Rate Limit Exceeded (HTTP 429)**:
  - *Title*: `Query Limit Reached`
  - *Message*: *"You have reached the limit of 10 assistant queries per minute. Please wait {seconds} seconds before asking another question."*
- **LLM Provider Offline / Replay Fallback**:
  - *Banner*: `[Replay Mode Active]`
  - *Message*: *"Live LLM connection unavailable. Showing pre-verified, deterministic responses from the peer-reviewed test suite."*

---

## 5. Mandatory Disclaimers and Attributions

### 5.1 NASA FIRMS Attribution (Mandatory)
Every page footer, data export dialog, and methodology header **must** include:
> *"We acknowledge the use of data and imagery from NASA's Fire Information for Resource Management System (FIRMS) (https://earthdata.nasa.gov/firms), part of the NASA Earth Observing System Data and Information System (EOSDIS). MODIS Collection 6.1 (Terra/Aqua) and VIIRS Collection 2 (S-NPP, NOAA-20, NOAA-21) active-fire products courtesy of NASA LANCE and the University of Maryland."*

### 5.2 Basemap & Boundary Attribution
> *"Administrative boundaries courtesy of geoBoundaries (CC0 1.0 Universal & CC BY 3.0 IGO). Basemap © OpenStreetMap contributors, © MapLibre."*

### 5.3 Advisory & Operational Safety Disclaimer (Non-Negotiable)
Featured prominently in the footer, modal dialogs, and alert subscription forms:
> *"NOTICE: PyroScope is an open scientific research and decision-support platform designed for retrospective analysis, pattern discovery, and early season awareness. It is NOT an operational tactical fire dispatch system or emergency evacuation service. In the event of an active wildfire threat, immediately contact the Bangladesh Fire Service and Civil Defence (emergency: 999 or 102) and the Ministry of Environment, Forest and Climate Change."*
