import csv
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from route_planner.models import FuelStation


class Command(BaseCommand):
    help = "Import the supplied OPIS fuel-price CSV into the local station catalogue."

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=Path, default=settings.BASE_DIR / "data" / "fuel-prices-for-be-assessment.csv")
        parser.add_argument("--replace", action="store_true")

    def handle(self, *args, **options):
        csv_path = options["csv"]
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")
        if FuelStation.objects.exists() and not options["replace"]:
            raise CommandError("Stations already exist. Use --replace to import a fresh catalogue.")
        if options["replace"]:
            FuelStation.objects.all().delete()
        with csv_path.open(newline="", encoding="utf-8-sig") as source:
            stations = [FuelStation(opis_truckstop_id=row["OPIS Truckstop ID"].strip(), name=row["Truckstop Name"].strip(), address=row["Address"].strip(), city=row["City"].strip(), state=row["State"].strip(), rack_id=row["Rack ID"].strip(), retail_price=row["Retail Price"].strip()) for row in csv.DictReader(source)]
        FuelStation.objects.bulk_create(stations, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Imported {len(stations)} fuel-station prices."))

