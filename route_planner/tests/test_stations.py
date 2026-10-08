from decimal import Decimal
from django.test import TestCase
from route_planner.models import FuelStation
from route_planner.services.geo import Point
from route_planner.services.stations import StationRepository


class StationRepositoryTests(TestCase):
    def test_finds_station_inside_route_corridor(self):
        FuelStation.objects.create(opis_truckstop_id="1", name="Route Station", address="1 Road", city="Austin", state="TX", rack_id="1", retail_price=Decimal("3.12"), latitude=30.2672, longitude=-97.7431)
        stations = StationRepository().near_route([Point(30.2, -97.8), Point(30.3, -97.7)], corridor_miles=15)
        self.assertEqual([station.name for station in stations], ["Route Station"])

