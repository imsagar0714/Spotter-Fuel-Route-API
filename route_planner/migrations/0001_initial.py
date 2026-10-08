from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="FuelStation", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("opis_truckstop_id", models.CharField(max_length=32)), ("name", models.CharField(max_length=255)), ("address", models.CharField(max_length=255)), ("city", models.CharField(max_length=128)), ("state", models.CharField(max_length=8)), ("rack_id", models.CharField(max_length=32)), ("retail_price", models.DecimalField(decimal_places=6, max_digits=8)), ("latitude", models.FloatField(blank=True, null=True)), ("longitude", models.FloatField(blank=True, null=True))], options={"ordering": ["state", "city", "name"]}),
        migrations.AddIndex(model_name="fuelstation", index=models.Index(fields=["latitude", "longitude"], name="route_plann_latitud_e48f11_idx")),
        migrations.AddIndex(model_name="fuelstation", index=models.Index(fields=["state", "city"], name="route_plann_state_30d23f_idx")),
    ]

