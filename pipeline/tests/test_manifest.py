from pathlib import Path

from pyroscope_pipeline.common.manifest import DatasetManifest, PipelineCounts, SourceManifest


def test_manifest_roundtrip(tmp_path: Path) -> None:
    manifest_file = tmp_path / "manifest.json"
    manifest = DatasetManifest(
        data_version="v0.1.0-test",
        git_commit="testcommit123",
        as_of_date="2026-11-10",
        parameters={"eps_spatial": 2700.0},
        sources=[
            SourceManifest(
                file_name="modis_test.csv",
                sensor="MODIS_TERRA",
                row_count=100,
                sha256="abc123hash",
                date_range=["2020-01-01", "2020-01-31"],
            )
        ],
        counts=PipelineCounts(detections_kept=100, events_created=10),
    )

    manifest.write_json(manifest_file)
    assert manifest_file.exists()

    loaded = DatasetManifest.read_json(manifest_file)
    assert loaded.data_version == "v0.1.0-test"
    assert loaded.counts.events_created == 10
    assert len(loaded.sources) == 1
    assert loaded.sources[0].sensor == "MODIS_TERRA"
