import io
import zipfile
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from route_planner.models import FuelStation

GEONAMES_US_URL = "https://download.geonames.org/export/dump/US.zip"


class Command(BaseCommand):
    help = "Assign approximate city-centre coordinates from GeoNames to imported US stations."

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path, help="Optional local GeoNames US.zip file.")

    def handle(self, *args, **options):
        source = options["source"] or settings.BASE_DIR / "data" / "geonames-us.zip"
        if source.exists():
            contents = source.read_bytes()
        else:
            try:
                response = requests.get(GEONAMES_US_URL, timeout=90)
                response.raise_for_status()
                contents = response.content
                source.write_bytes(contents)
            except requests.RequestException as error:
                raise CommandError(f"Could not download GeoNames data: {error}") from error

        cities = self._load_cities(contents)
        updated = []
        for station in FuelStation.objects.filter(latitude__isnull=True, longitude__isnull=True):
            city = cities.get((station.city.upper(), station.state.upper()))
            if city:
                station.latitude, station.longitude = city
                updated.append(station)
        with transaction.atomic():
            FuelStation.objects.bulk_update(updated, ["latitude", "longitude"], batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Assigned city-centre coordinates to {len(updated)} station records."))

    @staticmethod
    def _load_cities(contents: bytes) -> dict[tuple[str, str], tuple[float, float]]:
        cities: dict[tuple[str, str], tuple[int, float, float]] = {}
        with zipfile.ZipFile(io.BytesIO(contents)) as archive:
            with archive.open("US.txt") as source:
                for raw_line in source:
                    fields = raw_line.decode("utf-8").rstrip("\n").split("\t")
                    if len(fields) < 15 or fields[6] != "P":
                        continue
                    key = (fields[2].upper(), fields[10].upper())z
                    population = int(fields[14] or 0)
                    existing = cities.get(key)
                    if existing is None or population > existing[0]:
                        cities[key] = (population, float(fields[4]), float(fields[5]))
        return {key: (latitude, longitude) for key, (_, latitude, longitude) in cities.items()}
