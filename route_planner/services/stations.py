from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from route_planner.models import FuelStation
from route_planner.services.geo import Point, bounds, haversine_miles, sampled_route


@dataclass(frozen=True)
class StationCandidate:
    station_id: int
    name: str
    address: str
    city: str
    state: str
    price: Decimal
    point: Point
    route_mile: float
    distance_from_route_miles: float


class StationRepository:
    def closest_to_origin(self, origin: Point, maximum_distance_miles: float = 35) -> StationCandidate | None:
        closest: StationCandidate | None = None
        for station in FuelStation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            point = Point(station.latitude, station.longitude)
            distance = haversine_miles(origin, point)
            if distance <= maximum_distance_miles and (closest is None or distance < closest.distance_from_route_miles):
                closest = self._candidate(station, point, 0.0, distance)
        return closest

    def near_route(self, route_geometry: list[Point], corridor_miles: float = 25) -> list[StationCandidate]:
        samples = sampled_route(route_geometry)
        minimum_latitude, maximum_latitude, minimum_longitude, maximum_longitude = bounds(route_geometry)
        stations = FuelStation.objects.filter(latitude__isnull=False, longitude__isnull=False, latitude__gte=minimum_latitude, latitude__lte=maximum_latitude, longitude__gte=minimum_longitude, longitude__lte=maximum_longitude)
        candidates: list[StationCandidate] = []
        for station in stations:
            point = Point(station.latitude, station.longitude)
            sample, route_mile = min(samples, key=lambda item: haversine_miles(point, item[0]))
            distance = haversine_miles(point, sample)
            if distance <= corridor_miles:
                candidates.append(self._candidate(station, point, route_mile, distance))
        return sorted(candidates, key=lambda candidate: (candidate.route_mile, candidate.price))

    @staticmethod
    def _candidate(station: FuelStation, point: Point, route_mile: float, distance: float) -> StationCandidate:
        return StationCandidate(station.id, station.name, station.address, station.city, station.state, station.retail_price, point, route_mile, distance)

