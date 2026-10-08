from django.db import models


class FuelStation(models.Model):
    """A record from the supplied OPIS fuel-price file."""

    opis_truckstop_id = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=128)
    state = models.CharField(max_length=8)
    rack_id = models.CharField(max_length=32)
    retail_price = models.DecimalField(max_digits=8, decimal_places=6)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["latitude", "longitude"]), models.Index(fields=["state", "city"])]
        ordering = ["state", "city", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.city}, {self.state})"

