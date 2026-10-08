from decimal import Decimal, ROUND_HALF_UP

from route_planner.services.exceptions import PlanningError
from route_planner.services.optimizer import FuelOptimizer, MAX_RANGE_MILES, MPG
from route_planner.services.routing import RoutingClient
from route_planner.services.stations import StationRepository


class RoutePlanService:
    def __init__(self, routing_client=None, station_repository=None, optimizer=None):
        self.routing_client = routing_client or RoutingClient()
        self.station_repository = station_repository or StationRepository()
        self.optimizer = optimizer or FuelOptimizer()

    def build(self, start: str, finish: str) -> dict:
        start_point = self.routing_client.geocode_us_location(start)
        finish_point = self.routing_client.geocode_us_location(finish)
        route = self.routing_client.driving_route(start_point, finish_point)
        origin_station = self.station_repository.closest_to_origin(start_point)
        if not origin_station:
            raise PlanningError("No supplied fuel station with coordinates is available within 35 miles of the start. Import station coordinates before requesting route plans.")
        candidates = self.station_repository.near_route(route.geometry)
        plan = self.optimizer.plan(origin_station, candidates, route.distance_miles)
        return {
            "start": {"query": start, "latitude": start_point.latitude, "longitude": start_point.longitude},
            "finish": {"query": finish, "latitude": finish_point.latitude, "longitude": finish_point.longitude},
            "route": {"distance_miles": self._rounded(route.distance_miles), "estimated_duration_minutes": route.duration_minutes, "geometry": {"type": "LineString", "coordinates": [[point.longitude, point.latitude] for point in route.geometry]}},
            "vehicle": {"fuel_efficiency_mpg": int(MPG), "maximum_range_miles": int(MAX_RANGE_MILES), "tank_capacity_gallons": float(MAX_RANGE_MILES / MPG)},
            "fuel_stops": [{"name": purchase.station.name, "address": purchase.station.address, "city": purchase.station.city, "state": purchase.station.state, "latitude": purchase.station.point.latitude, "longitude": purchase.station.point.longitude, "route_mile": self._rounded(purchase.station.route_mile), "distance_from_route_miles": self._rounded(purchase.station.distance_from_route_miles), "price_per_gallon": float(purchase.station.price), "gallons_to_buy": self._rounded(purchase.gallons), "cost": float(purchase.cost)} for purchase in plan.purchases],
            "summary": {"total_fuel_gallons": self._rounded(plan.total_gallons), "total_fuel_cost": float(plan.total_cost), "currency": "USD", "candidate_stations_considered": len(candidates), "assumption": "The vehicle starts empty and purchases its first fuel at the closest supplied station within 35 miles of the origin."},
        }

    @staticmethod
    def _rounded(value: float | Decimal) -> float:
        return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

