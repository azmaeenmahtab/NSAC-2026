from pyroscope_pipeline.ingest.normalize import format_acq_time, map_sensor_tag


def test_format_acq_time_padding() -> None:
    assert format_acq_time("52") == "00:52"
    assert format_acq_time(52) == "00:52"
    assert format_acq_time("544") == "05:44"
    assert format_acq_time(544) == "05:44"
    assert format_acq_time("1330") == "13:30"
    assert format_acq_time(1330) == "13:30"
    assert format_acq_time("0") == "00:00"
    assert format_acq_time(0) == "00:00"


def test_map_sensor_tag() -> None:
    assert map_sensor_tag("MODIS", "Terra") == "MODIS_TERRA"
    assert map_sensor_tag("MODIS", "Aqua") == "MODIS_AQUA"
    assert map_sensor_tag("MODIS", "T") == "MODIS_TERRA"
    assert map_sensor_tag("MODIS", "A") == "MODIS_AQUA"
    assert map_sensor_tag("VIIRS", "N") == "VIIRS_SNPP"
    assert map_sensor_tag("VIIRS", "NPP") == "VIIRS_SNPP"
    assert map_sensor_tag("VIIRS", "S-NPP") == "VIIRS_SNPP"
    assert map_sensor_tag("VIIRS", "N20") == "VIIRS_NOAA20"
    assert map_sensor_tag("VIIRS", "N21") == "VIIRS_NOAA21"
