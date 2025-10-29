from django.conf import settings
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone

_client = InfluxDBClient(
    url=settings.INFLUX_URL,
    token=settings.INFLUX_TOKEN,
    org=settings.INFLUX_ORG,
    timeout=30_000,
)

_write = _client.write_api(write_options=SYNCHRONOUS)
_query = _client.query_api()

MEASUREMENT = "readings"

def write_reading(sensor_id: int, ts: datetime, value: float):
    """
    Записать одно измерение:
    - measurement: readings
    - tag: sensor_id
    - field: value (float)
    - time: ts (UTC)
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    p = (
        Point(MEASUREMENT)
        .tag("sensor_id", str(sensor_id))
        .field("value", float(value))
        .time(ts, WritePrecision.NS)
    )
    _write.write(bucket=settings.INFLUX_BUCKET, org=settings.INFLUX_ORG, record=p)

def latest_reading(sensor_id: int):
    """
    Вернёт последнее значение по времени для данного сенсора:
    (timestamp: datetime, value: float) или None.
    Схлопывает все группы (все теги) и берёт глобально последнее.
    """
    flux = f'''
from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
  |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> group(columns: [])            // убрать все группировки, чтобы last() был глобальным
  |> last()
  |> keep(columns: ["_time","_value"])
'''
    tables = _query.query(flux, org=settings.INFLUX_ORG)

    latest = None
    for table in tables:
        for rec in table.records:
            ts = rec.get_time()
            val = rec.get_value()
            if latest is None or ts > latest[0]:
                latest = (ts, float(val) if val is not None else None)

    return latest

def latest_value(sensor_id: int) -> float | None:
    flux = f'''
from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
  |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> group(columns: [])
  |> last()
  |> keep(columns: ["_value"])
'''
    tables = _query.query(flux, org=settings.INFLUX_ORG)
    for table in tables:
        for rec in table.records:
            val = rec.get_value()
            return float(val) if val is not None else None
    return None