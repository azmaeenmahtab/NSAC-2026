"""Build Bangladesh Fire Service reference station catalog from HDX / HOTOSM POI."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd  # type: ignore[import-untyped]
import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import Point, shape  # type: ignore[import-untyped]

from pyroscope_pipeline.common.paths import RAW_DIR, REFERENCE_DIR

HDX_POI_URL = (
    "https://production-raw-data-api.s3.amazonaws.com/ISO3/BGD/"
    "points_of_interest/hotosm_bgd_points_of_interest_osm_geojson.zip"
)
FSCD_HOTLINE = "102"
NATIONAL_EMERGENCY = "999"


def ensure_hdx_poi_zip(raw_dir: Path | None = None) -> Path:
    """Download and cache the HDX HOTOSM Bangladesh POI archive under `data/raw/boundaries/`."""
    bdir = (raw_dir or RAW_DIR) / "boundaries"
    bdir.mkdir(parents=True, exist_ok=True)
    dest = bdir / "hotosm_bgd_points_of_interest_osm_geojson.zip"
    if not dest.is_file():
        resp = httpx.get(HDX_POI_URL, follow_redirects=True, timeout=120.0)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    return dest


def extract_fire_station_features(geojson_bytes: bytes) -> list[dict[str, Any]]:
    """Extract and normalize fire_station features from HOTOSM GeoJSON bytes."""
    payload = json.loads(geojson_bytes.decode("utf-8"))
    rows: list[dict[str, Any]] = []

    for feat in payload.get("features", []):
        props = feat.get("properties") or {}
        if props.get("amenity") != "fire_station":
            continue
        geom_raw = feat.get("geometry")
        if not geom_raw:
            continue

        geom = shape(geom_raw)
        if geom.is_empty:
            continue
        centroid = geom.centroid
        lon = round(float(centroid.x), 6)
        lat = round(float(centroid.y), 6)

        raw_id = str(props.get("id") or f"{lat}_{lon}").replace("/", "-")
        station_id = f"FSCD-{raw_id}"

        raw_name = props.get("name_en") or props.get("name") or props.get("name_bn")
        adm3 = props.get("adm3_name")
        adm2 = props.get("adm2_name")
        if raw_name and str(raw_name).strip():
            name = str(raw_name).strip()
        elif adm3:
            name = f"{adm3} Fire Service & Civil Defence Station"
        elif adm2:
            name = f"{adm2} Fire Service & Civil Defence Station"
        else:
            name = "Fire Service & Civil Defence Station"

        phone = props.get("phone") or props.get("contact:phone") or None
        email = props.get("email") or props.get("contact:email") or None

        rows.append(
            {
                "station_id": station_id,
                "name": name,
                "adm1_name": str(props.get("adm1_name") or "").strip(),
                "adm2_name": str(adm2 or "").strip(),
                "adm3_name": str(adm3 or "").strip(),
                "lat": lat,
                "lon": lon,
                "hotline": FSCD_HOTLINE,
                "national_emergency": NATIONAL_EMERGENCY,
                "phone": str(phone).strip() if phone else None,
                "email": str(email).strip() if email else None,
                "source": "HDX HOTOSM Bangladesh POI",
                "verified": True,
            }
        )
    return rows


def assign_district_ids(
    stations_df: pd.DataFrame,
    regions_geojson_path: Path,
) -> pd.DataFrame:
    """Spatially join stations against ADM2 polygons in `regions.geojson` to assign `district_id`."""
    if stations_df.empty:
        out = stations_df.copy()
        out["district_id"] = pd.Series(dtype="string")
        out["district_name"] = pd.Series(dtype="string")
        out["division_id"] = pd.Series(dtype="string")
        return out

    reg_gdf = gpd.read_file(regions_geojson_path)
    adm2 = reg_gdf[reg_gdf["level"] == "adm2"][
        ["region_id", "name", "parent_id", "geometry"]
    ].copy()
    adm2 = adm2.rename(
        columns={"region_id": "district_id", "name": "district_name", "parent_id": "division_id"}
    )

    pts_gdf = gpd.GeoDataFrame(
        stations_df,
        geometry=[Point(lon, lat) for lon, lat in zip(stations_df["lon"], stations_df["lat"])],
        crs="EPSG:4326",
    )

    joined = gpd.sjoin(pts_gdf, adm2, how="left", predicate="within")
    joined = joined.drop_duplicates(subset=["station_id"])

    # Fallback: nearest ADM2 polygon for points right on river/coast borders
    missing_mask = joined["district_id"].isna()
    if missing_mask.any():
        missing_pts = pts_gdf.loc[
            pts_gdf["station_id"].isin(joined.loc[missing_mask, "station_id"])
        ]
        nearest = gpd.sjoin_nearest(
            missing_pts.to_crs("EPSG:32646"),
            adm2.to_crs("EPSG:32646"),
            how="left",
        ).drop_duplicates(subset=["station_id"])
        lookup = nearest.set_index("station_id")
        for idx, row in joined.loc[missing_mask].iterrows():
            sid = row["station_id"]
            if sid in lookup.index:
                joined.loc[idx, "district_id"] = lookup.loc[sid, "district_id"]
                joined.loc[idx, "district_name"] = lookup.loc[sid, "district_name"]
                joined.loc[idx, "division_id"] = lookup.loc[sid, "division_id"]

    result = pd.DataFrame(joined.drop(columns=["geometry", "index_right"], errors="ignore"))
    result["district_name"] = result["district_name"].fillna(result["adm2_name"])
    return result.sort_values("station_id", ignore_index=True)


def build_fire_stations_reference(
    reference_dir: Path | None = None,
    raw_dir: Path | None = None,
) -> Path:
    """Build `data/reference/fire_stations.parquet` from HDX HOTOSM POI archive."""
    ref_dir = reference_dir or REFERENCE_DIR
    zip_path = ensure_hdx_poi_zip(raw_dir=raw_dir)

    geojson_bytes = b""
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            if member.endswith(".geojson"):
                geojson_bytes = zf.read(member)
                break
    if not geojson_bytes:
        raise FileNotFoundError(f"No .geojson found inside {zip_path}")

    rows = extract_fire_station_features(geojson_bytes)
    df = pd.DataFrame(rows)
    df = assign_district_ids(df, ref_dir / "regions.geojson")

    ordered_cols = [
        "station_id",
        "name",
        "district_id",
        "district_name",
        "division_id",
        "adm1_name",
        "adm3_name",
        "lat",
        "lon",
        "hotline",
        "national_emergency",
        "phone",
        "email",
        "source",
        "verified",
    ]
    df = df[ordered_cols]

    schema = pa.schema(
        [
            ("station_id", pa.string()),
            ("name", pa.string()),
            ("district_id", pa.string()),
            ("district_name", pa.string()),
            ("division_id", pa.string()),
            ("adm1_name", pa.string()),
            ("adm3_name", pa.string()),
            ("lat", pa.float64()),
            ("lon", pa.float64()),
            ("hotline", pa.string()),
            ("national_emergency", pa.string()),
            ("phone", pa.string()),
            ("email", pa.string()),
            ("source", pa.string()),
            ("verified", pa.bool_()),
        ]
    )

    out_path = ref_dir / "fire_stations.parquet"
    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(table, out_path, compression="ZSTD", version="2.6")
    return out_path


if __name__ == "__main__":
    out = build_fire_stations_reference()
    tbl = pd.read_parquet(out)
    print(f"Wrote {len(tbl)} fire stations to {out} ({out.stat().st_size} bytes)")
    print(tbl[["station_id", "name", "district_id", "lat", "lon"]].head(5))
