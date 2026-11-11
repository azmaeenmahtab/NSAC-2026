import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("*/api/health", () => {
    return HttpResponse.json({
      status: "healthy",
      service: "PyroScope API",
      version: "0.1.0",
    });
  }),

  http.get("*/api/meta", () => {
    return HttpResponse.json({
      data: {
        dataVersion: "v0.1.0-fixtures",
        asOf: "2025-12-31",
        provisionalFrom: null,
        parametersSummary: {
          eps_spatial_meters: 2700.0,
          eps_temporal_hours: 24.0,
        },
        sources: [
          {
            file_name: "synthetic_modis.csv",
            sensor: "MODIS",
          },
        ],
        counts: {
          events_created: 302,
        },
        attribution: "NASA FIRMS active fire data; Team Singularity",
      },
      meta: {
        dataVersion: "v0.1.0-fixtures",
        asOf: "2025-12-31",
      },
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
          id: "BGD-ADM2-beta",
          name: "Beta District",
          level: "adm2",
          parent_id: "BGD",
          bbox: [91.0, 22.0, 92.0, 23.0],
          aliases: ["Beta"],
        },
      ],
      meta: {
        dataVersion: "v0.1.0-fixtures",
        asOf: "2025-12-31",
      },
    });
  }),
];
