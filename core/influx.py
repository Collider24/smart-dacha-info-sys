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

MEASUREMENT = "readings"  # имя измерения в Influx

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
    Получить последнее значение для сенсора.
    Возвращает (ts, value) или None.
    """
    flux = f'''
from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
  |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> last()
'''
    tables = _query.query(flux, org=settings.INFLUX_ORG)
    for table in tables:
        for rec in table.records:
            return (rec.get_time(), rec.get_value())
    return None

def window_stats(sensor_id: int, window_seconds: int):
    """
    Пример окна: среднее/мин/макс за окно (последние window_seconds).
    """
    flux = f'''
from(bucket: "{settings.INFLUX_BUCKET}")
  |> range(start: -{window_seconds}s)
  |> filter(fn: (r) => r["_measurement"] == "{MEASUREMENT}")
  |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> keep(columns: ["_time","_value"])
  |> yield(name:"raw")
'''
    return _query.query_data_frame(flux, org=settings.INFLUX_ORG)
