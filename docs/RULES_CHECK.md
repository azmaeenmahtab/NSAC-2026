# Rules Check & Hackathon Regulations

Recorded by Team Lead (@azmaeenmahtab) for Team Singularity, NASA Space Apps Challenge 2026.

---

### 1. May we write application code before Nov 14 09:00, or only research, data download and planning?
**Answer: YES, application code is permitted.**  
The local instructor and leads have reviewed our project setup and authorized our team to commence full implementation immediately. All `EVENT` chunks are officially unlocked and active.

---

### 2. Required submission fields, formats and limits
* **Project Title:** PyroScope: Harmonized Burning Activity Calendar
* **Short Project Summary:** Concise overview explaining how MODIS and VIIRS data are harmonized and how the FireCalendar serves early warning and wildland management.
* **Public Code Repository:** Public GitHub link to `https://github.com/azmaeenmahtab/NSAC-2026`.
* **Demonstration Video:** 240 seconds (4 minutes max) uploaded to YouTube/Vimeo.
* **Pitch Deck:** Slide presentation (PDF/Slides).
* **Space Agency Data Sources:** NASA FIRMS MODIS Collection 6.1 (Terra & Aqua) and VIIRS S-NPP Collection 2 hot spots.

---

### 3. Required disclosure of AI tools used
* **Disclosure Policy:** We disclose all AI tools utilized during development.
* **Tools Used:** Antigravity, Claude Code, Cursor, and Gemini API.
* **Implementation Integrity:** All scientific code, clustering algorithms, and data tables are validated with deterministic tests; the AI assistant runs strictly on typed function tools against verified Parquet data.

---

### 4. Local judging schedule, pitch length and whether a new video is needed
* **Pitch Length:** 240 seconds (4 minutes) live or pre-recorded pitch demonstration.
* **Demo Target:** Show the "hidden jump" chart in 2012, how PyroScope eliminates the jump, Chittagong Hill Tracts seasonal analysis, 3D hex map, and grounded "Ask PyroScope" assistant.

---

### 5. Judging criteria wording
Expected Space Apps global criteria:
1. **Impact:** How much does this solve the hotspot discrepancy for land managers and firefighters?
2. **Creativity:** How innovative is the FireCalendar and harmonization approach?
3. **Validity:** Is the scientific calibration mathematically sound, reproducible, and cross-validated?
4. **Relevance:** Does it directly address the NASA challenge "Harmonization of MODIS and VIIRS Hot Spots"?
5. **Presentation:** Quality and clarity of the demo, UI, and storytelling.

---

### 6. Rules on using existing open-source code and data
* Standard approved open-source libraries (`duckdb`, `pandas`, `h3`, `react-map-gl`, `deck.gl`, `fastapi`, `shadcn/ui`) are permitted.
* All data and boundaries are publicly sourced and attributed in `data/reference/SOURCES.md`.
* NASA FIRMS data attribution is maintained in the UI, API, and README.

---

### 7. Final submission time zone and cutoff
* **Time Zone:** Asia/Dhaka (UTC+6).
* **Hard Cutoff:** November 15, 2026 at 23:59 local time.
* **Internal Target:** Complete final deployment and submit by November 15 at 18:00 (giving a 6-hour buffer).
