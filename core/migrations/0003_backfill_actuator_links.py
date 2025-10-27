from django.db import migrations

def forwards(apps, schema_editor):
    Actuator = apps.get_model("core", "Actuator")
    SensorActuator = apps.get_model("core", "SensorActuator")

    for act in Actuator.objects.select_related("sensor__facility"):
        if act.sensor_id:
            SensorActuator.objects.get_or_create(
                sensor_id=act.sensor_id,
                actuator_id=act.id,
            )
            if act.sensor and act.sensor.facility_id and act.facility_id is None:
                act.facility_id = act.sensor.facility_id
                act.save(update_fields=["facility"])

def backwards(apps, schema_editor):
    SensorActuator = apps.get_model("core", "SensorActuator")
    SensorActuator.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_sensoractuator_alter_actuator_options_and_more"),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
