"""Automated browser benchmark for Spike A (MapLibre + deck.gl H3HexagonLayer, 30,000 r7 hexes).

Starts a local HTTP server serving a self-contained MapLibre + deck.gl + H3HexagonLayer page
with 30,000 real Bangladesh r7 H3 cells, launches local Chrome in headless WebGL mode, drives
pan/zoom and 2D/3D extrusion transitions, and reports measured first-render time, FPS, and
JS heap memory usage.
"""

from __future__ import annotations

import http.server
import json
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any

import h3

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def build_benchmark_html(cells: list[dict[str, Any]]) -> str:
    cells_json = json.dumps(cells)
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Spike A Deck.gl H3 Benchmark</title>
  <link href="https://unpkg.com/maplibre-gl@5.24.0/dist/maplibre-gl.css" rel="stylesheet" />
  <script src="https://unpkg.com/h3-js@4.5.0/dist/h3-js.umd.js"></script>
  <script src="https://unpkg.com/maplibre-gl@5.24.0/dist/maplibre-gl.js"></script>
  <script src="https://unpkg.com/deck.gl@9.4.1/dist.min.js"></script>
  <script src="https://unpkg.com/d3-color@3.1.0/dist/d3-color.min.js"></script>
  <script src="https://unpkg.com/d3-interpolate@3.0.1/dist/d3-interpolate.min.js"></script>
  <script src="https://unpkg.com/d3-scale-chromatic@3.1.0/dist/d3-scale-chromatic.min.js"></script>
  <style>html, body, #map {{ margin: 0; width: 1280px; height: 800px; background: #09090b; }}</style>
</head>
<body>
  <div id="map"></div>
  <script>
    const tStart = performance.now();
    const DATA = {cells_json};
    const P95 = 95;

    function infernoColor(v) {{
      const t = Math.max(0, Math.min(1, v / P95));
      const c = d3.rgb(d3.interpolateInferno(t));
      return [c.r, c.g, c.b, 215];
    }}

    const map = new maplibregl.Map({{
      container: 'map',
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [90.3563, 23.685],
      zoom: 7,
      pitch: 35,
      bearing: 0
    }});

    function makeLayer(extruded) {{
      return new deck.H3HexagonLayer({{
        id: 'pyroscope-h3-layer',
        data: DATA,
        pickable: true,
        filled: true,
        extruded: extruded,
        wireframe: false,
        stroked: false,
        elevationScale: extruded ? 60 : 0,
        getHexagon: d => d.h3,
        getFillColor: d => infernoColor(d.value),
        getElevation: d => d.value
      }});
    }}

    let firstRenderMs = null;
    const overlay = new deck.MapboxOverlay({{
      interleaved: false,
      layers: [makeLayer(true)],
      onAfterRender: () => {{
        if (firstRenderMs === null) {{
          firstRenderMs = Math.round(performance.now() - tStart);
        }}
      }}
    }});
    map.addControl(overlay);

    function measurePanZoom(durationMs) {{
      return new Promise(resolve => {{
        let frames = 0;
        const start = performance.now();
        function step(now) {{
          frames++;
          const elapsed = now - start;
          const phase = elapsed / durationMs;
          map.jumpTo({{
            center: [90.3563 + Math.sin(phase * 6.28) * 0.8, 23.685 + Math.cos(phase * 6.28) * 0.8],
            zoom: 7 + Math.sin(phase * 3.14) * 1.2
          }});
          if (elapsed < durationMs) {{
            requestAnimationFrame(step);
          }} else {{
            resolve(Math.round((frames * 1000) / elapsed * 10) / 10);
          }}
        }}
        requestAnimationFrame(step);
      }});
    }}

    map.once('load', async () => {{
      const h3GenStart = performance.now();
      const DataLen = DATA.length;
      if (firstRenderMs === null) {{
        firstRenderMs = Math.round(performance.now() - tStart);
      }}
      const fps3d = await measurePanZoom(1800);
      overlay.setProps({{ layers: [makeLayer(false)] }});
      const fps2d = await measurePanZoom(1800);
      const memBytes = performance.memory ? performance.memory.usedJSHeapSize : 0;
      const report = {{
        cell_count: DataLen,
        first_render_ms: firstRenderMs,
        fps_3d_extruded: fps3d,
        fps_2d_flat: fps2d,
        js_heap_mb: Math.round((memBytes / (1024 * 1024)) * 10) / 10,
        user_agent: navigator.userAgent
      }};
      await fetch('/report?data=' + encodeURIComponent(JSON.stringify(report)));
    }});
  </script>
</body>
</html>
"""


def run_benchmark() -> dict[str, Any]:
    center = h3.latlng_to_cell(23.685, 90.3563, 7)
    ring = sorted(h3.grid_disk(center, 110))[:30_000]
    cells = [{"h3": c, "value": ((i * 37) % 100) + 1} for i, c in enumerate(ring)]
    html_content = build_benchmark_html(cells).encode("utf-8")

    result_box: dict[str, Any] = {}
    done_event = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.startswith("/report"):
                qs = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(qs)
                result_box.update(json.loads(params["data"][0]))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                done_event.set()
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_content)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    chrome_bin = next((p for p in CHROME_CANDIDATES if Path(p).exists()), None)
    assert chrome_bin is not None, "Neither Chrome nor Edge found"

    proc = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu-vsync",
            "--enable-webgl",
            "--ignore-gpu-blocklist",
            "--enable-precise-memory-info",
            "--window-size=1280,800",
            f"http://127.0.0.1:{port}/",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        finished = done_event.wait(timeout=25.0)
        assert finished, "Timed out waiting for Chrome WebGL benchmark report"
    finally:
        proc.terminate()
        server.shutdown()
        time.sleep(0.2)

    return result_box


if __name__ == "__main__":
    metrics = run_benchmark()
    print("Spike A Browser Metrics:", json.dumps(metrics, indent=2))

