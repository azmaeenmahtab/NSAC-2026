# PyroScope Data Findings: Exploration of NASA FIRMS Archives (P02)

**Author**: @adityasaha03  
**Date**: 2026-11-11  
**Dataset**: NASA FIRMS MODIS Collection 6.1 (2000-11 to 2026-11) and VIIRS S-NPP Collection 2 (2012-01 to 2026-11) covering Bangladesh bounding box `[88.0, 20.5, 92.8, 26.7]`.  
**Script**: `spikes/explore/explore_firms.py` (run end-to-end against raw CSVs).

---

## 1. Row Counts per Sensor and per Year, and the VIIRS/MODIS Ratio

### Data Table: Annual Detections & VIIRS/MODIS Ratios (2000–2026)

| Year | MODIS Raw | VIIRS Raw | Raw Ratio (V/M) | MODIS Filtered | VIIRS Filtered | Filtered Ratio (V/M) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **2000** (Nov-Dec) | 22 | — | — | 15 | — | — |
| **2001** | 2,286 | — | — | 2,164 | — | — |
| **2002** | 838 | — | — | 744 | — | — |
| **2003** | 11,332 | — | — | 10,965 | — | — |
| **2004** | 12,640 | — | — | 12,213 | — | — |
| **2005** | 12,631 | — | — | 12,202 | — | — |
| **2006** | 17,593 | — | — | 16,939 | — | — |
| **2007** | 16,259 | — | — | 15,639 | — | — |
| **2008** | 10,253 | — | — | 9,889 | — | — |
| **2009** | 17,133 | — | — | 16,478 | — | — |
| **2010** | 14,129 | — | — | 13,554 | — | — |
| **2011** | 9,651 | — | — | 9,204 | — | — |
| **2012** | 12,775 | 42,813 | 3.35 | 12,318 | 38,966 | 3.16 |
| **2013** | 10,954 | 45,312 | 4.14 | 10,596 | 39,837 | 3.76 |
| **2014** | 11,448 | 56,738 | 4.96 | 10,967 | 48,615 | 4.43 |
| **2015** | 9,358 | 39,026 | 4.17 | 8,955 | 34,004 | 3.80 |
| **2016** | 8,493 | 33,157 | 3.90 | 8,198 | 29,387 | 3.58 |
| **2017** | 6,808 | 29,217 | 4.29 | 6,534 | 26,423 | 4.04 |
| **2018** | 8,868 | 32,596 | 3.68 | 8,477 | 29,326 | 3.46 |
| **2019** | 9,318 | 36,009 | 3.86 | 8,948 | 32,169 | 3.60 |
| **2020** | 10,790 | 39,358 | 3.65 | 10,254 | 34,383 | 3.35 |
| **2021** | 12,374 | 47,686 | 3.85 | 11,832 | 41,839 | 3.54 |
| **2022** | 6,507 | 32,430 | 4.98 | 6,177 | 28,672 | 4.64 |
| **2023** | 9,680 | 41,907 | 4.33 | 9,224 | 35,956 | 3.90 |
| **2024** | 7,648 | 32,175 | 4.21 | 7,311 | 28,054 | 3.84 |
| **2025** | 10,004 | 40,280 | 4.03 | 9,624 | 35,550 | 3.69 |
| **2026** (to Nov 1) | 4,920 | 23,751 | 4.83 | 4,729 | 21,403 | 4.53 |

### Findings & Report Verification
Over the full complete overlap period (2012–2025), annual raw MODIS detections average **9,645** (ranging from 6,507 to 12,775), while raw VIIRS S-NPP detections average **39,193** (ranging from 29,217 to 56,738). The research report claimed annual counts of "3,029 vs 10,972" for Bangladesh, which underestimates actual active-fire detections by a factor of roughly 3.2x to 3.6x. The actual ratio of VIIRS to MODIS raw detections in the overlap years averages **4.10x** (ranging between 3.35x in 2012 and 4.98x in 2022), and **3.77x** after applying standard science filters. The report's claim of "3 to 7 times" is accurate at the lower bound but exaggerated at the upper end, as the empirical detection ratio never exceeds 5.0x in any year.

---

## 2. Confidence Field Distribution and Quality Filtering

### Data Table: Confidence Classes & Impact of Filtering

| Sensor / Metric | Category / Condition | Count | Percentage | Filter Action |
| :--- | :--- | :---: | :---: | :--- |
| **MODIS Confidence** | Low (`< 30`) | 9,484 | 3.58% | Dropped |
| (Numeric 0–100, Mean: 70.66) | Nominal (`30–79`) | 158,493 | 59.87% | Retained |
| | High (`80–100`) | 96,735 | 36.54% | Retained |
| **MODIS Type** | Type 0 (Presumed vegetation) | 263,423 | 99.51% | Retained |
| | Type 2 (Other static land source) | 933 | 0.35% | Dropped |
| | Type 3 (Offshore detection) | 326 | 0.12% | Dropped |
| | NaN (NRT file, no type column) | 30 | 0.01% | Retained |
| **VIIRS Confidence** | Low (`l`) | 50,160 | 8.76% | Dropped |
| (Categorical string `l`, `n`, `h`) | Nominal (`n`) | 485,214 | 84.76% | Retained |
| | High (`h`) | 37,081 | 6.48% | Retained |
| **VIIRS Type** | Type 0 (Presumed vegetation) | 553,672 | 96.72% | Retained |
| | Type 2 (Other static land source) | 16,785 | 2.93% | Dropped |
| | Type 3 (Offshore detection) | 1,586 | 0.28% | Dropped |
| | NaN (NRT file, no type column) | 412 | 0.07% | Retained |

### Findings & Filter Comparison
MODIS confidence is recorded as an integer (0 to 100), where 59.87% of pixels are nominal (30–79) and 36.54% are high (>=80). In contrast, VIIRS confidence is strictly a categorical string (`l`, `n`, `h`), with 84.76% classified as nominal (`n`) and only 6.48% as high (`h`). Applying the project filter (MODIS >= 30, VIIRS `n` or `h`, and `type == 0` when present) safely drops **3.99%** of MODIS and **11.86%** of VIIRS detections while discarding false industrial and offshore sources. The research report proposed applying a `> 80%` threshold to both sensors; for MODIS, this would erroneously discard 65.28% of all valid active fires, while for VIIRS (which has string confidence), numeric comparison would cause an exception or drop 100% of data. The `type` column exists in all standard archive CSVs but is completely absent in Near-Real-Time (NRT) files, requiring pipeline filters to handle `NaN` gracefully.

---

## 3. Schema, Timestamp Formatting, Duplicates, and Spatial Bounds

### Data Table: Ingest Quality Diagnostics

| Attribute / Check | MODIS Archive & NRT | VIIRS S-NPP Archive & NRT | Resolution / Handling Rule |
| :--- | :--- | :--- | :--- |
| **Column Set (Archive)** | 15 columns (`latitude`, `longitude`, `brightness`, `scan`, `track`, `acq_date`, `acq_time`, `satellite`, `instrument`, `confidence`, `version`, `bright_t31`, `frp`, `daynight`, `type`) | Identical 15 columns | Match standard schema in `docs/DB_SCHEMA.md` |
| **Column Set (NRT)** | 14 columns (`type` column absent) | 14 columns (`type` column absent) | Impute `type = NaN` during ingestion |
| **`acq_time` representation** | Integer in CSV (e.g., `52`, `544`, `1422`) | Integer in CSV (e.g., `52`, `726`, `1942`) | Left-pad with zeros to 4 digits (`str.zfill(4)`) before ISO formatting |
| **Exact Duplicates** | 0 duplicates | 1 duplicate row | Drop duplicates on `(satellite, latitude, longitude, acq_ts)` |
| **Archive vs NRT Duplicates** | 0 duplicate detections | 0 duplicate detections | Archive and NRT temporal windows align cleanly without overlap |
| **Rows Outside Defined BBox** | 0 rows outside `[88.0, 20.5, 92.8, 26.7]` | 4 rows outside bounds (`lon > 92.8`) | Spatial clip during ingestion drops these 4 edge artifacts |

### Findings
Both MODIS and VIIRS standard CSV files share an identical set of 15 columns in the archive products and 14 columns in the NRT products. Acquisition times (`acq_time`) are encoded as integers representing `HHMM` with omitted leading zeros (for example, `52` denotes `00:52` UTC and `544` denotes `05:44` UTC), making a 4-character zero-pad mandatory during timestamp construction. Exact spatial-temporal duplicates are virtually nonexistent (0 for MODIS, 1 for VIIRS), and the transition from archive to NRT is completely disjoint with no duplicated timestamps. Only 4 VIIRS points out of 572,455 fall marginally outside the bounding box boundaries, confirming that the download geographic boundaries were accurate.

---

## 4. Temporal Coverage, Gaps, and the Overlap Period

### Data Table: Temporal Coverage Summary

| Metric | MODIS (Terra & Aqua) | VIIRS (S-NPP) | Pipeline Overlap Window |
| :--- | :---: | :---: | :---: |
| **Earliest Detection Date** | 2000-11-02 (Terra) | 2012-01-20 | 2012-01-20 |
| **Latest Detection Date** | 2026-11-01 (Aqua/Terra NRT) | 2026-11-01 (S-NPP NRT) | 2026-11-01 |
| **Total Span (Calendar Days)** | 9,496 days | 5,400 days | 5,400 days |
| **Days with >= 1 Fire Detection** | 4,960 days (52.2%) | 4,498 days (83.3%) | 4,498 days |
| **First Full Calendar Month** | **2000-12** (December 2000) | **2012-02** (February 2012) | **2012-02** |
| **Total Overlap Months** | 178 total months | 178 total months | **177 complete months** (2012-02 to 2026-10) |

### Findings
MODIS records begin on 2000-11-02, making **2000-12** the first complete calendar month with full 31-day coverage, although November 2000 contains valid detections starting from day 2. VIIRS S-NPP records begin on 2012-01-20, meaning January 2012 lacks the first 19 days of observations; therefore, the first complete calendar month for VIIRS is **2012-02**. The overlap period for calibration spans exactly **177 complete calendar months** from 2012-02 through 2026-10 (plus November 2026 partial). Days with zero fire detections are frequent during the summer monsoon (June–September) due to seasonal precipitation and heavy cloud cover rather than satellite data loss.

---

## 5. Day/Night Split and Fire Radiative Power (FRP) Distributions

### Data Table: Day vs. Night Frequency and Fire Radiative Power (MW)

| Sensor & Mode | Count | Share (%) | Min (MW) | p25 (MW) | Median (MW) | Mean (MW) | p75 (MW) | p90 (MW) | p95 (MW) | Max (MW) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MODIS Total** | 264,712 | 100.0% | 0.0 | 12.00 | **25.20** | **60.07** | 60.00 | 135.20 | 220.10 | 5,568.20 |
| *MODIS Day* | 251,182 | 94.89% | 0.0 | 12.60 | 26.60 | 62.38 | 63.00 | 140.50 | 227.30 | 5,568.20 |
| *MODIS Night* | 13,530 | 5.11% | 2.6 | 7.20 | 10.90 | 17.20 | 19.10 | 33.40 | 49.20 | 530.60 |
| **VIIRS Total** | 572,455 | 100.0% | 0.0 | 3.16 | **6.05** | **14.95** | 14.12 | 35.05 | 59.41 | 1,248.16 |
| *VIIRS Day* | 505,500 | 88.30% | 0.0 | 3.93 | 7.09 | 16.70 | 16.23 | 38.79 | 64.50 | 1,248.16 |
| *VIIRS Night* | 66,955 | 11.70% | 0.0 | 0.77 | 1.23 | 1.67 | 1.98 | 3.04 | 4.05 | 62.73 |

### Findings
Active-fire detections are overwhelmingly diurnal in Bangladesh, with daytime detections comprising 94.89% of MODIS and 88.30% of VIIRS hot spots. However, VIIRS detects more than double the proportion of nighttime fires compared to MODIS (11.70% vs. 5.11%) because its 375 m I-bands possess much higher thermal sensitivity to small smoldering burns under cool nocturnal ambient temperatures. Because a MODIS pixel covers roughly 7 times the ground area of a VIIRS 375 m pixel at nadir, MODIS integrates higher radiant heat, yielding a median FRP of 25.20 MW versus only 6.05 MW for VIIRS. Both sensors exhibit zero null values in their FRP fields, and daytime fires exhibit significantly higher radiative power than nighttime fires across all percentiles.

---

## 6. Chittagong Hill Tracts (CHT) Monthly Fire Seasonality

### Data Table: Monthly Fire Detections in Chittagong Hill Tracts Box (`[91.6, 21.2, 92.7, 23.8]`)

| Month | MODIS Filtered Count | MODIS Share (%) | VIIRS Filtered Count | VIIRS Share (%) | Season Flag |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **1 (Jan)** | 225 | 0.20% | 1,112 | 0.56% | Off-season |
| **2 (Feb)** | 1,611 | 1.40% | 3,196 | 1.61% | Pre-season ramp |
| **3 (Mar)** | 64,843 | **56.44%** | 105,170 | **52.86%** | **Peak Season** |
| **4 (Apr)** | 47,265 | **41.14%** | 86,249 | **43.35%** | **Peak Season** |
| **5 (May)** | 758 | 0.66% | 2,016 | 1.01% | Season taper |
| **6 (Jun)** | 17 | 0.01% | 98 | 0.05% | Monsoon quiet |
| **7 (Jul)** | 3 | <0.01% | 18 | <0.01% | Monsoon quiet |
| **8 (Aug)** | 1 | <0.01% | 22 | 0.01% | Monsoon quiet |
| **9 (Sep)** | 4 | <0.01% | 33 | 0.02% | Monsoon quiet |
| **10 (Oct)** | 13 | 0.01% | 140 | 0.07% | Monsoon quiet |
| **11 (Nov)** | 73 | 0.06% | 367 | 0.18% | Post-monsoon |
| **12 (Dec)** | 81 | 0.07% | 529 | 0.27% | Post-monsoon |
| **Total CHT** | **114,894** | **100.0%** | **198,950** | **100.0%** | **March–May: >97%** |

### Findings
The Chittagong Hill Tracts (CHT) is the primary burning hotspot of Bangladesh, accounting for **45.2% of all MODIS detections** and **39.4% of all VIIRS detections** in the entire country. The burning season in CHT is intensely concentrated: March and April alone account for 97.58% (MODIS) and 96.21% (VIIRS) of annual activity, rising to **98.23% (MODIS)** and **97.23% (VIIRS)** when including May. This acute peak corresponds to traditional *jhum* (slash-and-burn) clearing during the hottest dry pre-monsoon months. From June through October, persistent monsoon rains virtually extinguish burning across the hills, with fewer than 0.1% of annual hot spots recorded during these months.

---

## 7. Sensor Steps: Aqua Launch (2002) and S-NPP Satellite Stability

### Data Table: MODIS Satellite Platform Breakdown (Filtered Hotspots)

| Year | Terra Hotspots | Aqua Hotspots | Total MODIS | Aqua Share (%) | Notable Event |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **2000** | 15 | 0 | 15 | 0.0% | Terra operational (Nov 2) |
| **2001** | 2,164 | 0 | 2,164 | 0.0% | Terra single-platform baseline |
| **2002** | 611 | 133 | 744 | 17.9% | Aqua launched May 4, 2002 |
| **2003** | 658 | 10,307 | 10,965 | **94.0%** | Full dual-platform (Terra+Aqua) |
| **2004** | 1,035 | 11,178 | 12,213 | **91.5%** | Full dual-platform |
| **2005** | 727 | 11,475 | 12,202 | **94.0%** | Full dual-platform |
| **2006** | 2,725 | 14,214 | 16,939 | **83.9%** | Peak fire year |
| **2007** | 2,247 | 13,392 | 15,639 | **85.6%** | High fire year |

### Findings
A critical, previously unheralded artifact exists in the historical MODIS record: Terra overpasses in the late morning (~10:30 AM local time), whereas agricultural and forest clearing burns in Bangladesh ignite predominantly in early to mid-afternoon. When Aqua joined in late 2002 with its ~13:30 local afternoon overpass, detected hot spots soared from 2,164 in 2001 to 10,965 in 2003, with Aqua capturing **91% to 94% of all annual hot spots**. Consequently, 2000–2002 represents an under-sampled epoch in the MODIS record that must be transparently noted on the methodology page. Conversely, VIIRS S-NPP counts remain remarkably stable across 2016–2024 (averaging ~31,000 to ~36,000 filtered hot spots) with no artificial jumps in 2018 (NOAA-20 launch) or 2023 (NOAA-21 launch), fully validating Decision D-09 to use S-NPP as the sole calibration reference.

---

## 8. ST-DBSCAN Event Clustering Diagnostics and Sizing

### Data Table: ST-DBSCAN Cluster Characteristics (Eps: 2.7 km, Time Eps: 24 hr, MinPts: 2)

| Sensor | Benchmark Year | Total Pixels | Fire Events | Clustered Pixels | Noise Points | Noise Share (%) | Mean Pixels/Event | Runtime (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MODIS** | 2016 | 8,198 | **576** | 7,715 | 483 | 5.89% | 13.4 | 0.25 s |
| **VIIRS** | 2016 | 29,387 | **846** | 28,560 | 827 | 2.81% | 33.8 | 1.39 s |
| **MODIS** | 2019 | 8,948 | **571** | 8,434 | 514 | 5.74% | 14.8 | 0.16 s |
| **VIIRS** | 2019 | 32,169 | **862** | 31,286 | 883 | 2.74% | 36.3 | 1.75 s |
| **MODIS** | 2023 | 9,224 | **554** | 8,710 | 514 | 5.57% | 15.7 | 0.33 s |
| **VIIRS** | 2023 | 35,956 | **883** | 35,060 | 896 | 2.49% | 39.7 | 2.46 s |

### Findings
Applying Space-Time DBSCAN clustering (2,700 m spatial radius, 24-hour temporal window, `min_pts = 2`) aggregates multi-pixel hot spots into discrete physical fire events, condensing pixel volume by a factor of ~15x for MODIS and ~36x for VIIRS. Crucially, while raw pixel counts differ by nearly 4x, the number of distinct physical fire events differs by only **1.47x to 1.59x** (approximately 560 MODIS events vs. 860 VIIRS events per year), proving that the majority of the "hidden jump" in raw satellite data is a pixel-resolution artifact rather than hundreds of unobserved independent fires. Noise points (isolated single-pixel flashes that do not repeat in space or time) represent only 5.6%–5.9% of MODIS pixels and 2.5%–2.8% of VIIRS pixels. The pure BallTree clustering algorithm executes in under 2.5 seconds per year on modern hardware, confirming that the entire 26-year historical pipeline can run in under 45 seconds total.

---

## 9. Decision on NOAA-20 Sensitivity Check (P2)

**Decision**: **NOAA-20 sensitivity check remains strictly a P2 optional stretch task and will NOT be included in the P0/P1 core harmonization pipeline.**  
**Justification**:
1. Our exploration proves that S-NPP provides an unbroken, highly consistent, single-sensor record from February 2012 to the present day without artificial multi-satellite jumps.
2. Incorporating NOAA-20 (operational 2018) into the historical pipeline would inject another artificial step change at 2018, violating the core scientific mission of providing a seamless Burning Activity Calendar.
3. S-NPP alone provides sufficient spatial density (~35,000 filtered detections/year) to calibrate against MODIS without needing secondary satellites.

