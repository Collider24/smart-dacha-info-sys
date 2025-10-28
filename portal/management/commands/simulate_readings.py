import random
import time

from django.core.management.base import BaseCommand
from django.utils import timezone as djtz

from core.models import Sensor
from core import influx

_last_written = {}

def pick_value(sensor):
    if sensor.min_val is not None and sensor.max_val is not None:
        return random.uniform(sensor.min_val, sensor.max_val)
    return random.gauss(50.0, 10.0)

class Command(BaseCommand):
    help = "Пишет псевдослучайные показания в InfluxDB только для активных датчиков."

    def add_arguments(self, parser):
        parser.add_argument("--tick", type=float, default=1.0,
                            help="Шаг цикла в секундах (по умолчанию 1.0)")
        parser.add_argument("--once", action="store_true",
                            help="Сделать один проход по активным датчикам и выйти")

    def handle(self, *args, **opts):
        tick = opts["tick"]
        once = opts["once"]

        self.stdout.write(self.style.SUCCESS(
            f"Старт симулятора: tick={tick}s once={once}"
        ))

        while True:
            now = djtz.now()
            active = list(Sensor.objects.filter(is_active=True).only(
                "id","sampling_s","min_val","max_val"
            ))
            for s in active:
                last = _last_written.get(s.id)
                due = last is None or (now - last).total_seconds() >= max(1, s.sampling_s)
                if not due:
                    continue
                value = pick_value(s)
                influx.write_reading(sensor_id=s.id, ts=now, value=value)
                print(f"Writing to {s.id} value: {value} ")
                _last_written[s.id] = now

            if once:
                break
            time.sleep(tick)
