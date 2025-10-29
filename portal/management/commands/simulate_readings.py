import random
import time
from typing import Callable, Dict, Union, Tuple, Iterable

import numpy as np
from django.core.management.base import BaseCommand
from django.utils import timezone as djtz

from core.models import Sensor
from core import influx

_last_written: Dict[int, 'datetime'] = {}

def home_temperature(x, s=None):
    return np.sin(x * np.pi / 12 - np.pi / 2) * 10.0 + 20.0 + np.random.normal(scale=1/50)

def power_consumption(x, s=None):
    value = np.sin(x * np.pi / 12 - np.pi / 2) * 7500 + 5000 + np.random.normal(scale=5000)
    np.clip(value, 0, 15000, out=value)
    return value

def rare_bool(x, s=None):
    value = np.random.randint(0, 200)
    return 1 if value == 24 else 0

def morning_evening_bool(x, s=None):
    if 8 < x < 10 or 19 < x < 22:
        value = np.random.randint(0, 30)
        return 1 if value == 24 else 0
    else:
        value = np.random.randint(0, 200)
        return 1 if value == 24 else 0

def humidity(x, s=None):
    value = np.sin(x * np.pi / 12) * 40 + 50 + np.random.normal(scale=2.5)
    np.clip(value, 0,100, out=value)
    return value

def co2(x, s=None):
    value = 1000 + np.random.normal(scale=(np.sin(x) + 1) * 1000)
    value = np.clip(value, 400, 5000, out=value)
    return value

def temp_sauna_parnaya(x, s=None):
    if 19 < x < 21:
        return  np.sin(x * np.pi - 3 * np.pi / 2) * 39 + 60 + np.random.normal(scale=0.1)
    else:
        return  20 + np.random.normal(scale=0.1)

def temp_sauna_predparnaya(x, s=None):
    if 19 < x < 21:
        return  np.sin(x * np.pi - 3 * np.pi / 2) * 10 + 30 + np.random.normal(scale=0.1)
    else:
        return  20 + np.random.normal(scale=0.1)

def temp_sauna_pipe(x, s=None):
    if 19 < x < 23:
        return np.sin(x * np.pi / 2 - 2 * np.pi) * 200 + 220 + np.random.normal(scale=0.1)
    else:
        return 20 + np.random.normal(scale=0.1)

def co2_sauna(x, s=None):
    if 19 < x < 21:
        return  np.clip(np.sin(x * np.pi - 3 * np.pi / 2) * 125 + 125 + np.random.normal(scale=30), 0, 500)
    else:
        return  5 + np.random.normal(scale=0.1)

def woodshed_weight(x, s):
    rec = influx.latest_reading(s.id)
    now = djtz.now()

    if rec is None:
        dt_hours = max((s.sampling_s or 1) / 3600.0, 0.0)
        base_val = None
    else:
        rec_ts, rec_val = rec
        dt_hours = (now - rec_ts).total_seconds() / 3600.0
        if dt_hours < 0:
            dt_hours = 0.0
        dt_hours = max(dt_hours, (s.sampling_s or 1) / 3600.0)
        base_val = rec_val

    if base_val is None or (isinstance(base_val, float) and np.isnan(base_val)) or base_val == 0:
        return float(np.clip(3000.0 - np.random.uniform(0, 10), 0, 3000))

    dec = np.random.uniform(0, 2) * dt_hours
    return float(np.clip(float(base_val) - dec, 0, 3000))


def humidity_ground(x, s):
    rec = influx.latest_reading(s.id)
    now = djtz.now()

    if rec is None:
        dt_hours = max((s.sampling_s or 1) / 3600.0, 0.0)
        base_val = None
    else:
        rec_ts, rec_val = rec
        dt_hours = (now - rec_ts).total_seconds() / 3600.0
        if dt_hours < 0:
            dt_hours = 0.0
        dt_hours = max(dt_hours, (s.sampling_s or 1) / 3600.0)
        base_val = rec_val

    if base_val is None or (isinstance(base_val, float) and np.isnan(base_val)) or base_val == 0:
        return float(np.clip(100.0 - np.random.uniform(0, 10), 0, 100))

    dec = np.random.uniform(8, 10) * dt_hours
    return float(np.clip(float(base_val) - dec, 0, 100))


def water_level_pool(x, s=None):
    return (s.min_val + s.max_val) / 2 + np.random.normal(scale=50)

def water_level_zero(x, s=None):
    return 0

def greenhouse_temperature(x, s=None):
    return np.sin(x * np.pi / 12 - np.pi / 2) * 10.0 + 20.0 + np.random.normal(scale=1/50)

def outside_temperature(x, s=None):
    return np.sin(x * np.pi / 12 - np.pi / 2) * 10.0 + 15.0 + np.random.normal(scale=1/50)

def pool_temperature(x, s=None):
    return np.sin(x * np.pi / 12 + 14 * np.pi / 12) * 10.0 + 15.0 + np.random.normal(scale=1/50)

def garage_temperature(x, s=None):
    return np.sin(x * np.pi / 12 + 4 * np.pi / 3) * 7.0 + 15.0 + np.random.normal(scale=1/50)

def cellar_temperature(x, s=None):
    return np.sin(x * np.pi / 12 + 4 * np.pi / 3) * 2 + 4 + np.random.normal(scale=1 / 50)

def illumination(x, s=None):
    return np.sin(x * np.pi / 12 - np.pi / 2) * 1250.0 + 1300 + np.random.normal(scale=1/50)


SimulatorRegistry: Dict[Union[Tuple[int, str], str, int], Callable[[float], float]] = {
    "Главный дом [house]:Температура (внутри)": home_temperature,
    "Главный дом [house]:Потребляемая мощность": power_consumption,
    "Главный дом [house]:Утечка воды": rare_bool,
    "Главный дом [house]:Дым": rare_bool,
    "Главный дом [house]:Влажность (внутри)" : humidity,
    "Главный дом [house]:CO2" : co2,

    "Баня [sauna]:Утечка воды" : rare_bool,
    "Баня [sauna]:Температура парной": temp_sauna_parnaya,
    "Баня [sauna]:Температура предбанника": temp_sauna_predparnaya,
    "Баня [sauna]:Температура дымохода": temp_sauna_pipe,
    "Баня [sauna]:Влажность парной": temp_sauna_parnaya,
    "Баня [sauna]:Угарный газ": co2_sauna,

    "Бассейн у бани [pool]:Уровень воды": water_level_pool,
    "Бассейн у бани [pool]:Температура воды": pool_temperature,

    "Полиэтиленовая теплица [greenhouse]:Температура воздуха" : greenhouse_temperature,
    "Полиэтиленовая теплица [greenhouse]:Влажность почвы" : humidity_ground,

    "Стеклянная теплица [greenhouse]:Температура воздуха" : greenhouse_temperature,
    "Стеклянная теплица [greenhouse]:Освещённость" : illumination,
    "Стеклянная теплица [greenhouse]:Влажность почвы" : humidity_ground,

    "Уличный парник [greenhouse]:Температура воздуха": greenhouse_temperature,
    "Уличный парник [greenhouse]:Влажность почвы": humidity_ground,

    "Погреб в доме [cellar]:Уровень воды": water_level_zero,
    "Погреб в доме [cellar]:Температура": cellar_temperature,
    
    "Гриль-зона с костровым местом [grill]:Датчик пламени": morning_evening_bool,

    "Дровеник [woodshed]:Датчик движения" : morning_evening_bool,
    "Дровеник [woodshed]:Масса запаса" : woodshed_weight,
    "Дровеник [woodshed]:Температура" : outside_temperature,

    "Крытый гараж [garage]:Положение ворот" : morning_evening_bool,
    "Крытый гараж [garage]:Температура" : garage_temperature,

    "Открытый настил [garage]:Температура" : outside_temperature,

    "Яма в гараже [cellar]:Уровень воды" : water_level_zero,
}

def _pick_random(sensor: Sensor) -> float:
    if sensor.min_val is not None and sensor.max_val is not None:
        return np.clip(np.random.normal(loc=(sensor.min_val + sensor.max_val) / 2,
                                        scale=(sensor.min_val + sensor.max_val) / 8), sensor.min_val, sensor.max_val)
    return random.gauss(50.0, 10.0)

def _now_hours_local(now) -> float:
    lt = djtz.localtime(now)
    return (lt.hour
            + lt.minute / 60.0
            + lt.second / 3600.0
            + lt.microsecond / 3_600_000_000.0)

def _sensor_key_candidates(s: Sensor) -> Iterable[Union[Tuple[int, str], str, int]]:

    yield (s.facility_id, s.name)

    yield str(s)

    yield s.id

    yield s.name

def _value_for_sensor(s: Sensor, now) -> float:
    x = _now_hours_local(now)

    func = None
    for k in _sensor_key_candidates(s):
        func = SimulatorRegistry.get(k)
        if func:
            break

    if func:
        try:
            val = float(func(x, s))
        except Exception as e:
            print(f"[WARN] Failed for '{s}' (ID={s.id}): {e}. Fallback to rand value.")
            val = _pick_random(s)
    else:
        val = _pick_random(s)

    if s.min_val is not None:
        val = max(val, s.min_val)
    if s.max_val is not None:
        val = min(val, s.max_val)
    return val


class Command(BaseCommand):
    help = "Пишет псевдослучайные/сценарные показания в InfluxDB для активных датчиков."

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

            active = list(
                Sensor.objects.filter(is_active=True)
                .select_related("facility")
                .only("id", "sampling_s", "min_val", "max_val", "name", "facility")
            )

            for s in active:
                last = _last_written.get(s.id)
                due = last is None or (now - last).total_seconds() >= max(1, s.sampling_s)
                if not due:
                    continue

                value = _value_for_sensor(s, now)
                influx.write_reading(sensor_id=s.id, ts=now, value=value)

                print(f"Writing to {s.id} '{s}' value={value:.6f}")
                _last_written[s.id] = now

            if once:
                break
            time.sleep(tick)