import json
from pathlib import Path

import pandas as pd

from pyroscope_pipeline.common.paths import REFERENCE_DIR
from pyroscope_pipeline.reference.build_stations import extract_fire_station_features


def test_extract_fire_station_features_pure() -> None:
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [92.18, 22.65]},
                "properties": {
                    "id": "node/123",
                    "amenity": "fire_station",
                    "name": "Rangamati Fire Station",
                    "adm1_name": "Chattogram",
                    "adm2_name": "Rangamati",
                },
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [90.40, 23.80]},
                "properties": {
                    "id": "node/456",
                    "amenity": "hospital",
                    "name": "Ignored Hospital",
                },
            },
        ],
    }
    rows = extract_fire_station_features(json.dumps(sample_geojson).encode("utf-8"))
    assert len(rows) == 1
    assert rows[0]["station_id"] == "FSCD-node-123"
    assert rows[0]["name"] == "Rangamati Fire Station"
    assert rows[0]["hotline"] == "102"
    assert rows[0]["national_emergency"] == "999"


def test_fire_stations_reference_parquet() -> None:
    path = Path(REFERENCE_DIR) / "fire_stations.parquet"
    assert path.is_file()
    df = pd.read_parquet(path)
    assert len(df) >= 150
    assert df["district_id"].isna().sum() == 0
    assert (df["lat"].between(20.0, 27.0)).all()
    assert (df["lon"].between(88.0, 93.0)).all()
    assert df["station_id"].is_unique
    assert (df["hotline"] == "102").all()
