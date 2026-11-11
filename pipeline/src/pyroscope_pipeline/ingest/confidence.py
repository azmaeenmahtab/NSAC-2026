"""Pure functions for confidence and type filtering of satellite detections."""

import pandas as pd


def filter_modis(
    df: pd.DataFrame,
    min_confidence: int = 30,
    require_type_zero: bool = True,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Filter MODIS detections by numeric confidence and fire type.

    Returns:
        (filtered_df, dropped_counts_by_reason)
    """
    dropped_counts = {
        "low_confidence": 0,
        "non_vegetation_type": 0,
    }

    if df.empty:
        return df.copy(), dropped_counts

    # 1. Confidence filter (>= min_confidence)
    # Convert confidence to numeric if string
    conf = pd.to_numeric(df["confidence"], errors="coerce").fillna(0)
    conf_mask = conf >= min_confidence
    dropped_counts["low_confidence"] = int((~conf_mask).sum())

    # 2. Type filter (type == 0 when present; keep if type column is missing/NaN)
    if require_type_zero and "type" in df.columns:
        type_series = pd.to_numeric(df["type"], errors="coerce")
        # type is 0 or NaN (NRT)
        type_mask = type_series.isna() | (type_series == 0)
        # only count as dropped by non_vegetation if it passed confidence
        dropped_type = int((conf_mask & (~type_mask)).sum())
        dropped_counts["non_vegetation_type"] = dropped_type
        keep_mask = conf_mask & type_mask
    else:
        keep_mask = conf_mask

    filtered = df.loc[keep_mask].copy()
    return filtered, dropped_counts


def filter_viirs(
    df: pd.DataFrame,
    allowed_confidence: tuple[str, ...] = ("n", "h"),
    require_type_zero: bool = True,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Filter VIIRS detections by categorical confidence (nominal, high) and fire type.

    Returns:
        (filtered_df, dropped_counts_by_reason)
    """
    dropped_counts = {
        "low_confidence": 0,
        "non_vegetation_type": 0,
    }

    if df.empty:
        return df.copy(), dropped_counts

    # 1. Confidence filter: categorical 'n' or 'h' (drop 'l')
    conf_str = df["confidence"].astype(str).str.strip().str.lower()
    conf_mask = conf_str.isin(allowed_confidence)
    dropped_counts["low_confidence"] = int((~conf_mask).sum())

    # 2. Type filter (type == 0 when present; keep if type column is missing/NaN)
    if require_type_zero and "type" in df.columns:
        type_series = pd.to_numeric(df["type"], errors="coerce")
        type_mask = type_series.isna() | (type_series == 0)
        dropped_type = int((conf_mask & (~type_mask)).sum())
        dropped_counts["non_vegetation_type"] = dropped_type
        keep_mask = conf_mask & type_mask
    else:
        keep_mask = conf_mask

    filtered = df.loc[keep_mask].copy()
    return filtered, dropped_counts


def get_confidence_class(sensor_family: str, raw_confidence: pd.Series) -> pd.Series:
    """Map raw confidence to standard confidence_class ('nominal' or 'high')."""
    if sensor_family == "MODIS":
        num_conf = pd.to_numeric(raw_confidence, errors="coerce").fillna(0)
        return pd.Series(
            ["high" if c >= 80 else "nominal" for c in num_conf],
            index=raw_confidence.index,
            dtype="string",
        )
    else:
        # VIIRS ('h' -> 'high', 'n' -> 'nominal')
        str_conf = raw_confidence.astype(str).str.strip().str.lower()
        return pd.Series(
            ["high" if c == "h" else "nominal" for c in str_conf],
            index=raw_confidence.index,
            dtype="string",
        )
