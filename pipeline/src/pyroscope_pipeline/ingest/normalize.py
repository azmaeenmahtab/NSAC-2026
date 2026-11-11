"""Pure functions for timestamp and sensor normalization per DB_SCHEMA.md."""

import pandas as pd


def format_acq_time(raw_time: str | float) -> str:
    """Format FIRMS acq_time into HH:MM string with zero padding.

    Examples:
        52 -> "00:52"
        544 -> "05:44"
        1330 -> "13:30"
        0 -> "00:00"
    """
    if pd.isna(raw_time):
        return "00:00"

    # Convert to integer string without decimal
    try:
        clean_val = int(float(raw_time))
    except (ValueError, TypeError):
        clean_val = 0

    val_str = str(clean_val).zfill(4)
    if len(val_str) > 4:
        val_str = val_str[:4]

    return f"{val_str[:2]}:{val_str[2:]}"


def map_sensor_tag(sensor_family: str, satellite: str) -> str:
    """Map FIRMS satellite field to standardized sensor tag."""
    sat = str(satellite).strip().upper()

    if sensor_family == "MODIS":
        if "TERRA" in sat or sat == "T":
            return "MODIS_TERRA"
        if "AQUA" in sat or sat == "A":
            return "MODIS_AQUA"
        return "MODIS_TERRA"

    elif sensor_family == "VIIRS":
        if sat in ("N", "NPP", "S-NPP", "SNPP"):
            return "VIIRS_SNPP"
        if "20" in sat or sat == "N20":
            return "VIIRS_NOAA20"
        if "21" in sat or sat == "N21":
            return "VIIRS_NOAA21"
        return "VIIRS_SNPP"

    return f"{sensor_family}_{sat}"


def normalize_detection_records(
    df: pd.DataFrame,
    sensor_family: str,
    source_file: str,
) -> pd.DataFrame:
    """Normalize raw FIRMS detections into standard schema."""
    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame(index=df.index)

    # Coordinates
    out["lat"] = pd.to_numeric(df["latitude"], errors="coerce")
    out["lon"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Sensor tags
    out["sensor_family"] = sensor_family
    satellites = df["satellite"] if "satellite" in df.columns else "UNKNOWN"
    out["sensor"] = [map_sensor_tag(sensor_family, s) for s in satellites]

    # Timestamps
    date_strs = df["acq_date"].astype(str).str.strip()
    time_strs = [format_acq_time(t) for t in df["acq_time"]]
    ts_strings = date_strs + " " + time_strs + ":00"
    out["acq_ts"] = pd.to_datetime(ts_strings, utc=True, errors="coerce")

    # Day / Night
    out["daynight"] = df["daynight"].astype(str).str.strip().str.upper()

    # Confidence
    out["confidence_raw"] = df["confidence"].astype(str).str.strip()
    from pyroscope_pipeline.ingest.confidence import get_confidence_class

    out["confidence_class"] = get_confidence_class(sensor_family, df["confidence"])

    # Fire Radiative Power (frp_mw)
    out["frp_mw"] = pd.to_numeric(df["frp"], errors="coerce")

    # Pixel geometry
    out["scan"] = pd.to_numeric(df["scan"], errors="coerce")
    out["track"] = pd.to_numeric(df["track"], errors="coerce")

    # Version and source file
    out["version"] = df["version"].astype(str).str.strip() if "version" in df.columns else "unknown"
    out["source_file"] = source_file

    return out
