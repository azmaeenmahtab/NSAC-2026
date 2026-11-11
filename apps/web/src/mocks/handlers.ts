import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("*/api/health", () => {
    return HttpResponse.json({
      status: "healthy",
      service: "PyroScope API",
      version: "0.1.0",
      dataLoaded: true,
      dataVersion: "v0.1.0-fixtures",
    });
  }),

  http.get("*/api/meta", () => {
    return HttpResponse.json({
      data: {
        dataVersion: "v0.1.0-fixtures",
        asOf: "2025-12-31",
        provisionalFrom: "2025-06-01",
        parametersSummary: { eps_spatial_meters: 2700.0, eps_temporal_hours: 24.0 },
        sources: [
          { file_name: "synthetic_modis.csv", sensor: "MODIS" },
          { file_name: "synthetic_viirs.csv", sensor: "VIIRS" },
        ],
        counts: { events_created: 302 },
        attribution:
          "NASA FIRMS active fire data; Team Singularity; CARTO / OpenStreetMap basemaps; geoBoundaries CC-BY 3.0 IGO.",
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/areas", () => {
    return HttpResponse.json({
      data: [
        {
          id: "BGD",
          name: "Bangladesh",
          level: "country",
          parent_id: null,
          bbox: [88.0, 20.5, 92.8, 26.7],
          aliases: ["Bangladesh", "BD"],
        },
        {
          id: "BGD-ADM2-alpha",
          name: "Alpha District",
          level: "adm2",
          parent_id: "BGD",
          bbox: [89.0, 22.0, 90.0, 23.0],
          aliases: ["Alpha"],
        },
        {
          id: "PRESET-CHT",
          name: "Chittagong Hill Tracts",
          level: "preset",
          parent_id: "BGD",
          bbox: [91.8, 21.5, 92.8, 23.8],
          aliases: ["CHT", "Hill Tracts"],
        },
      ],
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/heatmap", () => {
    return HttpResponse.json({
      data: {
        res: 7,
        metric: "harmonized",
        from: "2020-01",
        to: "2020-12",
        cells: [
          { h3: "87642825fffffff", value: 42, frp_mw: 125.4, lat: 22.5, lon: 92.2 },
          { h3: "87642824fffffff", value: 18, frp_mw: 45.2, lat: 22.6, lon: 92.3 },
        ],
        stats: { min: 0, p50: 18, p95: 42, max: 42, sum: 60, count: 2 },
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/series", () => {
    return HttpResponse.json({
      data: [
        {
          year: 2020,
          month: 1,
          raw_modis: 12,
          raw_viirs: 45,
          naive_splice: 45,
          harmonized: 15,
          in_overlap: true,
          source_used: "viirs_calibrated",
          provisional: false,
        },
        {
          year: 2020,
          month: 2,
          raw_modis: 25,
          raw_viirs: 90,
          naive_splice: 90,
          harmonized: 30,
          in_overlap: true,
          source_used: "viirs_calibrated",
          provisional: false,
        },
      ],
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/calendar", () => {
    return HttpResponse.json({
      data: {
        grid: [
          { year: 2020, month: 1, value: 15, class: "normal", percentile_rank: 55 },
          { year: 2020, month: 2, value: 30, class: "normal", percentile_rank: 70 },
          { year: 2020, month: 3, value: 140, class: "extreme", percentile_rank: 97 },
        ],
        climatology: [
          { month: 1, mean: 12, p50: 10, p90: 25, p95: 35 },
          { month: 2, mean: 24, p50: 20, p90: 45, p95: 60 },
          { month: 3, mean: 85, p50: 75, p90: 120, p95: 135 },
        ],
        season: { start_month: 2, peak_month: 3, end_month: 5, share_of_annual: 0.85 },
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/stats/yearly", () => {
    return HttpResponse.json({
      data: [
        { year: 2020, total_events: 185, total_frp_mw: 540.2, peak_month: 3, rank: 3 },
        { year: 2021, total_events: 210, total_frp_mw: 620.0, peak_month: 3, rank: 1 },
      ],
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/anomalies", () => {
    return HttpResponse.json({
      data: [
        {
          year: 2020,
          month: 3,
          value: 140,
          class: "extreme",
          percentile_rank: 97,
          baseline_p95: 135,
          excess_events: 5,
        },
      ],
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/methodology", () => {
    return HttpResponse.json({
      data: {
        method: "quantile_mapping",
        calibration_window: "2012-2026",
        naive_ratio: 2.988,
        harmonized_ratio: 1.0,
        jump_reduction_pct: 100.0,
        r2_overlap: 0.96,
        mape_pct: 7.2,
        limitations: [
          "ST-DBSCAN clustering assumes satellite detections within 2.7 km and 24 hours form one physical event",
          "VIIRS S-NPP saturation and false alarms near gas flares are filtered by landcover masks",
        ],
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),
];
