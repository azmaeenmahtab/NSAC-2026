import pandas as pd

from pyroscope_pipeline.ingest.confidence import filter_modis, filter_viirs, get_confidence_class


def test_modis_confidence_and_type_filter() -> None:
    data = {
        "confidence": [29, 30, 80, 100, 25, 45],
        "type": [0, 0, 0, 2, 0, 3],  # 2 and 3 are non-vegetation
    }
    df = pd.DataFrame(data)

    filtered, drop_reasons = filter_modis(df, min_confidence=30, require_type_zero=True)

    # Kept: rows 1 (30, type 0) and 2 (80, type 0)
    assert len(filtered) == 2
    assert list(filtered["confidence"]) == [30, 80]
    assert drop_reasons["low_confidence"] == 2  # rows 0 and 4 (29 and 25)
    assert drop_reasons["non_vegetation_type"] == 2  # rows 3 (type 2) and 5 (type 3)


def test_modis_missing_type_column_is_retained() -> None:
    data = {"confidence": [20, 50, 90]}
    df = pd.DataFrame(data)

    filtered, drop_reasons = filter_modis(df, min_confidence=30, require_type_zero=True)
    assert len(filtered) == 2
    assert list(filtered["confidence"]) == [50, 90]
    assert drop_reasons["low_confidence"] == 1


def test_viirs_confidence_filter() -> None:
    data = {
        "confidence": ["l", "n", "h", "L", "N", "H", "invalid"],
        "type": [0, 0, 0, 0, 2, 0, 0],
    }
    df = pd.DataFrame(data)

    filtered, drop_reasons = filter_viirs(df, allowed_confidence=("n", "h"), require_type_zero=True)

    # Kept: row 1 ('n', 0), row 2 ('h', 0), row 5 ('H', 0)
    assert len(filtered) == 3
    assert drop_reasons["low_confidence"] == 3  # 'l', 'L', 'invalid'
    assert drop_reasons["non_vegetation_type"] == 1  # row 4 ('N', type 2)


def test_confidence_class_mapping() -> None:
    modis_conf = pd.Series([20, 50, 80, 95])
    classes = get_confidence_class("MODIS", modis_conf)
    assert list(classes) == ["nominal", "nominal", "high", "high"]

    viirs_conf = pd.Series(["l", "n", "h", "N", "H"])
    classes_v = get_confidence_class("VIIRS", viirs_conf)
    assert list(classes_v) == ["nominal", "nominal", "high", "nominal", "high"]
