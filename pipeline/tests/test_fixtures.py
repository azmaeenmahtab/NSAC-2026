import hashlib
from pathlib import Path

from pyroscope_pipeline.fixtures.make_fixtures import generate_fixtures


def _compute_dir_hashes(directory: Path) -> dict[str, str]:
    hashes = {}
    for p in sorted(directory.glob("*.parquet")):
        hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def test_fixtures_determinism(tmp_path: Path) -> None:
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    generate_fixtures(dir1)
    generate_fixtures(dir2)

    hashes1 = _compute_dir_hashes(dir1)
    hashes2 = _compute_dir_hashes(dir2)

    assert hashes1 == hashes2
    assert "harmonized_region.parquet" in hashes1
    assert "harmonized_cell.parquet" in hashes1
