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
    // Generate fixture series for Alpha District showing 3x jump between 2011 and 2012
    const seriesData = [
      {
        year: 2011,
        month: 5,
        raw_modis: 100,
        raw_viirs: null,
        naive_splice: 100,
        harmonized: 100,
        in_overlap: false,
        source_used: "modis_raw",
        provisional: false,
      },
      {
        year: 2012,
        month: 5,
        raw_modis: 100,
        raw_viirs: 300,
        naive_splice: 300,
        harmonized: 100,
        in_overlap: true,
        source_used: "viirs_calibrated",
        provisional: false,
      },
      {
        year: 2020,
        month: 5,
        raw_modis: 200,
        raw_viirs: 600,
        naive_splice: 600,
        harmonized: 200,
        in_overlap: true,
        source_used: "viirs_calibrated",
        provisional: false,
      },
      {
        year: 2025,
        month: 12,
        raw_modis: 10,
        raw_viirs: 30,
        naive_splice: 30,
        harmonized: 10,
        in_overlap: true,
        source_used: "viirs_calibrated",
        provisional: true,
      },
    ];

    return HttpResponse.json({
      data: seriesData,
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/calendar", () => {
    return HttpResponse.json({
      data: {
        grid: [
          { year: 2020, month: 1, value: 10, class: "normal", percentile_rank: 45, provisional: false },
          { year: 2020, month: 2, value: 10, class: "normal", percentile_rank: 45, provisional: false },
          { year: 2020, month: 3, value: 20, class: "normal", percentile_rank: 55, provisional: false },
          { year: 2020, month: 4, value: 80, class: "elevated", percentile_rank: 92, provisional: false },
          { year: 2020, month: 5, value: 200, class: "extreme", percentile_rank: 99, provisional: false },
          { year: 2020, month: 6, value: 60, class: "normal", percentile_rank: 75, provisional: false },
          { year: 2020, month: 7, value: 10, class: "normal", percentile_rank: 50, provisional: false },
          { year: 2020, month: 8, value: 10, class: "normal", percentile_rank: 50, provisional: false },
          { year: 2020, month: 9, value: 10, class: "normal", percentile_rank: 50, provisional: false },
          { year: 2020, month: 10, value: 10, class: "normal", percentile_rank: 50, provisional: false },
          { year: 2020, month: 11, value: 10, class: "normal", percentile_rank: 50, provisional: false },
          { year: 2020, month: 12, value: 10, class: "normal", percentile_rank: 50, provisional: false },
          { year: 2025, month: 12, value: 10, class: "normal", percentile_rank: 50, provisional: true },
        ],
        climatology: [
          { month: 1, mean: 10, p50: 10, p90: 15, p95: 20 },
          { month: 2, mean: 10, p50: 10, p90: 15, p95: 20 },
          { month: 3, mean: 20, p50: 20, p90: 30, p95: 40 },
          { month: 4, mean: 80, p50: 80, p90: 90, p95: 100 },
          { month: 5, mean: 100, p50: 100, p90: 120, p95: 140 },
          { month: 6, mean: 60, p50: 60, p90: 75, p95: 85 },
          { month: 7, mean: 10, p50: 10, p90: 15, p95: 20 },
          { month: 8, mean: 10, p50: 10, p90: 15, p95: 20 },
          { month: 9, mean: 10, p50: 10, p90: 15, p95: 20 },
          { month: 10, mean: 10, p50: 10, p90: 15, p95: 20 },
          { month: 11, mean: 10, p50: 10, p90: 15, p95: 20 },
          { month: 12, mean: 10, p50: 10, p90: 15, p95: 20 },
        ],
        season: { start_month: 4, peak_month: 5, end_month: 6, share_of_annual: 0.706 },
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
