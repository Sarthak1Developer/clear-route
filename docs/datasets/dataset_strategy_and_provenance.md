# ClearRoute — Dataset Strategy, Provenance & Governance

## 1. Ethical Data Policy & Anti-Fabrication Principles

ClearRoute adheres strictly to academic and scientific integrity:
1. **Zero Fabrication**: Synthetic random numbers disguised as real sensor readings are strictly forbidden. If sensor coverage for a particular corridor or hour is absent, the system displays an explicit empty state detailing dataset boundaries.
2. **Provenance Transparency**: Every data point in the analytical tier traces back to an authentic public data repository or verified government record.
3. **Temporal Partitioning**: 2019 historical data is strictly used for model training; 2026 contextual data is isolated to forward-looking scenario modeling.

---

## 2. Historical Datasets (2019 Baseline & Training)

### A. Uber Movement India Traffic Dataset
- **Archive Source**: Zenodo Open Science Repository (`Uber Movement Speed and Travel Time Data for Indian Metropolitan Cities`).
- **Temporal Coverage**: April 1, 2019 – December 31, 2019.
- **Granularity**: Hourly aggregations by Traffic Analysis Zones (TAZ) and major arterial road segments.
- **Attributes Captured**: Segment identifier, mean travel time, harmonic mean speed (km/h), geometric zone bounds.

### B. Road Infrastructure Dataset (OpenStreetMap / Geofabrik)
- **Source**: Geofabrik India Regional OSM Extracts & OpenStreetMap Overpass API.
- **Content**:
  - Highway classification (`motorway`, `trunk`, `primary`, `secondary`, `tertiary`).
  - Physical attributes: Number of lanes, speed limits, surface type, one-way constraints.
  - Spatial mapping: LineStrings and bounding coordinates matched to Uber Movement segment centroids.

### C. Meteorological Records (Open-Meteo Historical ERA5)
- **Source**: Open-Meteo Historical Weather API (backed by ECMWF ERA5 reanalysis).
- **Parameters**:
  - `temperature_2m` (°C)
  - `precipitation` (mm)
  - `relative_humidity_2m` (%)
  - `wind_speed_10m` (km/h)
- **Temporal Alignment**: Resampled to UTC+05:30 (IST) hourly intervals matching traffic timestamps.

### D. Road Accident Context (MoRTH India)
- **Source**: Ministry of Road Transport and Highways (MoRTH), Government of India: *Road Accidents in India 2019*.
- **Role**: Contextual accident density indicator by metropolitan corridor.
- **Note**: Accident statistics are utilized as static contextual road safety indicators, not dynamic real-time emergency reports.

### E. Curated 2019 Holidays and Major Events
- **Source**: The Gazette of India (Public Holidays 2019), Municipal Cultural Calendars, and BCCI Cricket Schedule 2019.
- **Key Occasions Included**:
  - National: Republic Day, Independence Day, Gandhi Jayanti, Diwali (Oct 27, 2019), Eid ul-Fitr (Jun 5, 2019), Christmas (Dec 25, 2019).
  - City-Specific: Durga Puja (Kolkata, Oct 4–8, 2019), Ganesh Chaturthi (Mumbai, Sep 2–12, 2019), Chhath Puja (Delhi, Nov 2, 2019).

---

## 3. Forward-Looking 2026 Contextual Datasets

The 2026 pipeline enables future scenario analysis without polluting historical baseline weights:
- **Public Events**: Ticketmaster API (where active) and curated city calendar feeds for major concerts, cricket matches, and trade expos.
- **Public Holidays**: Official Gazette of India 2026 holiday calendar.
- **Weather Forecasts**: Open-Meteo 7-day numerical weather prediction models (GFS/ECMWF blends).
- **Manual Scenario Builder**: Allows urban planners to test hypothetical events (e.g., "What if an unseasonal 45mm storm hits Whitefield at 6 PM?").

---

## 4. Supported Cities & Benchmark Location Inventory

| City | Benchmark Locations | Latitude | Longitude | Primary Road Class |
| :--- | :--- | :---: | :---: | :--- |
| **Delhi** | Laxmi Nagar | 28.6304 | 77.2773 | Primary Arterial (Vikas Marg) |
| | Connaught Place | 28.6315 | 77.2167 | Central Commercial Ring (Radial Roads) |
| | Karol Bagh | 28.6514 | 77.1907 | Secondary Commercial |
| | Hauz Khas | 28.5494 | 77.2001 | Arterial (Outer Ring Road) |
| | Nehru Place | 28.5492 | 77.2518 | Commercial Trunk Corridor |
| **Mumbai** | Andheri East / West | 19.1136 | 72.8697 | Major Arterial (SV Road / WEH) |
| | Bandra Kurla Complex (BKC)| 19.0657 | 72.8687 | Financial District Secondary |
| | Dadar TT Circle | 19.0178 | 72.8478 | Central Intermodal Junction |
| | Powai | 19.1176 | 72.9060 | Secondary Arterial (JVLR) |
| | Borivali | 19.2288 | 72.8541 | Western Express Highway Trunk |
| **Bengaluru** | Whitefield | 12.9698 | 77.7499 | Tech Corridor Arterial |
| | Koramangala | 12.9352 | 77.6245 | Mixed Commercial / Residential |
| | Indiranagar | 12.9784 | 77.6408 | 100 Feet Road Commercial |
| | Electronic City | 12.8399 | 77.6770 | Hosur Road Expressway & Service Road |
| | Central Silk Board Junction| 12.9177 | 77.6238 | Major Bottleneck Highway Junction |
| **Hyderabad** | HITEC City | 17.4435 | 78.3772 | Cyberabad Tech Corridor |
| | Gachibowli | 17.4401 | 78.3489 | Financial District Outer Ring |
| | Banjara Hills | 17.4156 | 78.4350 | Primary Commercial Road No. 1 |
| | Begumpet | 17.4447 | 78.4664 | Sardar Patel Road Arterial |
| | Secunderabad Station Area | 17.4399 | 78.4983 | Intercity Transit Hub |
| **Kolkata** | Salt Lake Sector V | 22.5804 | 88.4378 | IT Hub Major Arterial |
| | Park Street | 22.5535 | 88.3524 | Central Hospitality & Cultural Core |
| | Howrah Station Approach | 22.5857 | 88.3426 | Howrah Bridge Transit Corridor |
| | New Town Action Area I | 22.5878 | 88.4688 | Major Arterial Expressway |
| | Esplanade | 22.5645 | 88.3516 | Central Kolkata Metro Interchange |
