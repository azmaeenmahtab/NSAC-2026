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
          "NASA FIRMS active fire data; Team Perceptron; CARTO / OpenStreetMap basemaps; geoBoundaries CC-BY 3.0 IGO.",
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
        {
          year: 2020,
          harmonized_total: 185.0,
          total_events: 185,
          frp_sum: 540.2,
          total_frp_mw: 540.2,
          peak_month: 3,
          rank: 3,
          vs_mean_pct: 12.5,
        },
        {
          year: 2021,
          harmonized_total: 210.0,
          total_events: 210,
          frp_sum: 620.0,
          total_frp_mw: 620.0,
          peak_month: 3,
          rank: 1,
          vs_mean_pct: 27.8,
        },
        {
          year: 2022,
          harmonized_total: 145.0,
          total_events: 145,
          frp_sum: 410.5,
          total_frp_mw: 410.5,
          peak_month: 4,
          rank: 5,
          vs_mean_pct: -11.9,
        },
        {
          year: 2023,
          harmonized_total: 195.0,
          total_events: 195,
          frp_sum: 580.0,
          total_frp_mw: 580.0,
          peak_month: 3,
          rank: 2,
          vs_mean_pct: 18.6,
        },
        {
          year: 2024,
          harmonized_total: 160.0,
          total_events: 160,
          frp_sum: 470.0,
          total_frp_mw: 470.0,
          peak_month: 3,
          rank: 4,
          vs_mean_pct: -2.8,
        },
      ],
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/guidance", () => {
    return HttpResponse.json({
      data: [
        {
          id: "g-01",
          stage: "in_season",
          audience: "community",
          text: "Clear 10m defensible space around residential perimeters and remove dry slash.",
          source_title: "Bangladesh Forest Department Wildfire Guidelines",
          source_url: "http://bforest.gov.bd/guidelines",
          verified: true,
        },
        {
          id: "g-02",
          stage: "in_season",
          audience: "land_manager",
          text: "Restrict agricultural residue burning during daytime peak thermal inversion hours.",
          source_title: "FAO Agricultural Fire Management Manual",
          source_url: "https://www.fao.org/forestry/fire-management",
          verified: true,
        },
        {
          id: "g-03",
          stage: "in_season",
          audience: "responder",
          text: "Pre-stage rapid response water tenders in high-risk H3 clusters.",
          source_title: "Local Forest Beat Emergency SOP",
          source_url: "https://bforest.gov.bd/sop",
          verified: false,
        },
        {
          id: "g-04",
          stage: "pre_season",
          audience: "community",
          text: "Inspect community water sources and establish village communication phone trees.",
          source_title: "Community Wildfire Preparedness Guide",
          source_url: "https://bforest.gov.bd/prep",
          verified: true,
        },
        {
          id: "g-05",
          stage: "extreme",
          audience: "responder",
          text: "Activate mutual aid agreements and establish daily aerial/satellite detection patrols.",
          source_title: "National Disaster Management Protocol",
          source_url: "https://modmr.gov.bd/protocol",
          verified: true,
        },
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
        parameters: {
          confidence_filter: "nominal_or_high",
          eps_spatial_meters: 2700,
          eps_temporal_hours: 24,
          min_pts: 2,
          h3_resolutions: [5, 6, 7],
          season_share: 0.7,
          cv_method: "leave_one_year_out",
          overlap_start: "2012-02",
          calibration_units_count: 65,
        },
        calibration_summary: [
          {
            unit_id: "BGD",
            name: "National (Bangladesh)",
            method: "quantile_mapping",
            fallback: false,
            rmse: 4.2,
            bias: -0.1,
            rank_corr: 0.97,
          },
          {
            unit_id: "BGD-ADM2-alpha",
            name: "Alpha District",
            method: "quantile_mapping",
            fallback: false,
            rmse: 2.1,
            bias: 0.05,
            rank_corr: 0.98,
          },
          {
            unit_id: "BGD-ADM2-beta",
            name: "Beta District",
            method: "regional_ratio",
            fallback: true,
            rmse: 6.8,
            bias: -0.4,
            rank_corr: 0.89,
            flag: "Low sample size, fallback applied",
          },
        ],
        jump_metrics: {
          naive_ratio: 2.988,
          harmonized_ratio: 1.0,
          overlap_cv_rmse: 4.2,
          overlap_cv_bias: -0.1,
          rank_correlation: 0.97,
        },
        qq_data: [
          { quantile: 0.05, modis: 5, viirs_raw: 15, viirs_harmonized: 5 },
          { quantile: 0.25, modis: 12, viirs_raw: 36, viirs_harmonized: 12 },
          { quantile: 0.50, modis: 28, viirs_raw: 84, viirs_harmonized: 28 },
          { quantile: 0.75, modis: 65, viirs_raw: 195, viirs_harmonized: 65 },
          { quantile: 0.90, modis: 120, viirs_raw: 360, viirs_harmonized: 120 },
          { quantile: 0.95, modis: 180, viirs_raw: 540, viirs_harmonized: 180 },
          { quantile: 0.99, modis: 240, viirs_raw: 720, viirs_harmonized: 240 },
        ],
        limitations: [
          "Active-fire counts are not burned area. Harmonized counts are 'MODIS-equivalent fire events', not hectares.",
          "The calibration assumes the MODIS-VIIRS relationship observed in 2012-present also holds before 2012 (it cannot be tested there).",
          "MODIS is itself not homogeneous: Aqua joined Terra in mid-2002, and Terra/Aqua orbits have drifted. We report this as a limitation and test sensitivity if time allows.",
          "Cloud, smoke and underground fires are under-detected by both sensors.",
          "Harmonization quality is measured by agreement over the overlap period (leave-one-year-out CV), not by the absence of change; real trends can remain.",
          "Alerts and guidance are advisory, not an official warning system.",
        ],
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.post("*/api/ask", async ({ request }) => {
    const body = (await request.json()) as { question?: string; area_id?: string; style?: string };
    const q = body.question || "";

    if (q.includes("trigger_429")) {
      return new HttpResponse(
        JSON.stringify({
          error: {
            code: "RATE_LIMITED",
            message: "Rate limit exceeded: max 10 queries per minute",
          },
        }),
        {
          status: 429,
          headers: {
            "Content-Type": "application/json",
            "Retry-After": "30",
          },
        }
      );
    }

    if (q.includes("trigger_502")) {
      return new HttpResponse(
        JSON.stringify({
          error: {
            code: "UPSTREAM_ERROR",
            message: "Upstream model provider timeout connecting to LLM service",
          },
        }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    let answerText =
      "In Chittagong Hill Tracts (PRESET-CHT), fire activity peaks strongly between March and April. In 2020, May experienced an extreme anomaly with 200 physical fire events.";

    if (q.includes("xss_test")) {
      answerText =
        "<script>alert('xss')</script><img onerror=\"alert(1)\" src=\"x\"/> In Chittagong Hill Tracts, peak burning occurs in March.";
    }

    return HttpResponse.json({
      data: {
        answer: answerText,
        mode: "replay",
        citations: [
          {
            tool: "get_season",
            areaId: "PRESET-CHT",
            years: [2012, 2013, 2014, 2015, 2016],
            dataVersion: "v0.1.0-fixtures",
          },
          {
            tool: "get_anomalies",
            areaId: "PRESET-CHT",
            years: [2020],
            dataVersion: "v0.1.0-fixtures",
          },
        ],
        toolCalls: [
          {
            name: "get_season",
            args: { area_id: "PRESET-CHT" },
            durationMs: 35.2,
          },
          {
            name: "get_anomalies",
            args: { area_id: "PRESET-CHT", year: 2020 },
            durationMs: 48.6,
          },
        ],
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/alerts/active", ({ request }) => {
    const url = new URL(request.url);
    const areaId = url.searchParams.get("area_id") || "PRESET-CHT";

    if (areaId.includes("quiet") || areaId === "BGD-ADM1-barisal") {
      return HttpResponse.json({
        data: {
          season_approaching: false,
          above_normal: false,
          current_month_class: "normal",
          days_until_season: null,
          reason: null,
          provisional_as_of: "2026-10-31",
        },
        meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
      });
    }

    return HttpResponse.json({
      data: {
        season_approaching: true,
        above_normal: true,
        current_month_class: "elevated",
        days_until_season: 12,
        reason: "Dry seasonal transition detected. Burning elevated above 90th percentile.",
        provisional_as_of: "2026-10-31",
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.post("*/api/alerts/subscriptions", async ({ request }) => {
    const body = (await request.json()) as {
      email?: string;
      area_id?: string;
      rule?: string;
      lead_days?: number;
    };

    if (!body.email || !body.email.includes("@")) {
      return new HttpResponse(
        JSON.stringify({
          error: {
            code: "VALIDATION_ERROR",
            message: "A valid email address is required.",
          },
        }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    if (body.email.includes("429")) {
      return new HttpResponse(
        JSON.stringify({
          error: {
            code: "RATE_LIMITED",
            message: "Subscription rate limit reached: maximum 5 requests per hour.",
          },
        }),
        {
          status: 429,
          headers: {
            "Content-Type": "application/json",
            "Retry-After": "3600",
          },
        }
      );
    }

    if (body.area_id === "unknown_area") {
      return new HttpResponse(
        JSON.stringify({
          error: {
            code: "NOT_FOUND",
            message: "Specified area identifier not found.",
          },
        }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      );
    }

    return HttpResponse.json({
      data: {
        message: "Verification email sent. Please check your inbox to confirm subscription.",
        status: "pending_confirmation",
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/alerts/subscriptions/confirm", ({ request }) => {
    const url = new URL(request.url);
    const token = url.searchParams.get("token");

    if (!token || token === "expired") {
      return new HttpResponse(
        JSON.stringify({
          error: {
            code: "TOKEN_EXPIRED",
            message: "This subscription link has expired or is invalid.",
          },
        }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    return HttpResponse.json({
      data: {
        confirmed: true,
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.delete("*/api/alerts/subscriptions", () => {
    return HttpResponse.json({
      data: {
        unsubscribed: true,
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),

  http.get("*/api/stations/nearby", () => {
    return HttpResponse.json({
      data: {
        center_lat: 22.65,
        center_lon: 92.18,
        location_source: "selected_area",
        area_id: "PRESET-CHT",
        area_name: "Chittagong Hill Tracts",
        threat: {
          level: "HIGH",
          headline: "Elevated Fire Activity",
          explanation:
            "Recent fires were spotted near this area, or activity is higher than normal.",
          nearby_recent_events: 2,
        },
        stations: [
          {
            station_id: "FSCD-node-5776723114",
            name: "Rangamati Fire Service & Civil Defence Station",
            district_id: "BGD-ADM2-rangamati",
            district_name: "Rangamati",
            lat: 22.6512,
            lon: 92.1849,
            distance_km: 0.5,
            hotline: "102",
            national_emergency: "999",
            phone: null,
            email: null,
            dial_number: "102",
            email_subject: "[HIGH Risk] Fire Alert Report Near Rangamati",
            email_body:
              "Hello Rangamati Fire Service & Civil Defence Station,\n\nI am reporting a possible fire near Rangamati.\n\n- Location: 22.6500N, 92.1800E\n- Current Area Risk: HIGH (Elevated Fire Activity)\n\nPlease check this location when possible.\n",
          },
          {
            station_id: "FSCD-way-531425078",
            name: "Khagrachhari Fire Service Station",
            district_id: "BGD-ADM2-khagrachari",
            district_name: "Khagrachari",
            lat: 23.112,
            lon: 91.9704,
            distance_km: 55.6,
            hotline: "102",
            national_emergency: "999",
            phone: null,
            email: null,
            dial_number: "102",
            email_subject: "[HIGH Risk] Fire Alert Report Near Khagrachari",
            email_body:
              "Hello Khagrachhari Fire Service Station,\n\nI am reporting a possible fire near Khagrachari.",
          },
        ],
      },
      meta: { dataVersion: "v0.1.0-fixtures", asOf: "2025-12-31" },
    });
  }),
];
