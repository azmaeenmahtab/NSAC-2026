export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  useMocks: process.env.NEXT_PUBLIC_USE_MOCKS === "true",
  basemapStyleUrl:
    process.env.NEXT_PUBLIC_BASEMAP_STYLE_URL ||
    "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
};

