from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from route_planner.services.exceptions import PlanningError
from route_planner.services.stations import StationCandidate

MPG = Decimal("10")
MAX_RANGE_MILES = Decimal("500")
TANK_CAPACITY_GALLONS = MAX_RANGE_MILES / MPG


@dataclass(frozen=True)
class FuelPurchase:
    station: StationCandidate
    gallons: Decimal
    cost: Decimal


@dataclass(frozen=True)
class FuelPlan:
    purchases: list[FuelPurchase]
    total_gallons: Decimal
    total_cost: Decimal


@dataclass(frozen=True)
class _Node:
    station: StationCandidate | None
    route_mile: Decimal

    @property
    def price(self) -> Decimal | None:
        return self.station.price if self.station else None


class FuelOptimizer:
    """Minimum-cost greedy refueling for ordered stations and a fixed tank capacity."""

    def plan(self, origin_station: StationCandidate, route_stations: list[StationCandidate], route_distance_miles: float) -> FuelPlan:
        destination_mile = Decimal(str(route_distance_miles))
        nodes = self._build_nodes(origin_station, route_stations, destination_mile)
        purchases: list[FuelPurchase] = []
        index = 0
        fuel_in_tank = Decimal("0")
        while index < len(nodes) - 1:
            current = nodes[index]
            if current.station is None:
                break
            reachable = [node for node in nodes[index + 1:] if node.route_mile - current.route_mile <= MAX_RANGE_MILES]
            if not reachable:
                raise PlanningError(f"No supplied fuel station is reachable within {MAX_RANGE_MILES} miles near route mile {current.route_mile}.")
            destination = next((node for node in reachable if node.station is None), None)
            cheaper = next((node for node in reachable if node.station and node.price < current.price), None)
            if destination:
                next_node, required_fuel = destination, self._gallons_between(current, destination)
            elif cheaper:
                next_node, required_fuel = cheaper, self._gallons_between(current, cheaper)
            else:
                next_node = min((node for node in reachable if node.station), key=lambda node: (node.price, -node.route_mile))
                required_fuel = TANK_CAPACITY_GALLONS
            gallons_to_buy = max(Decimal("0"), required_fuel - fuel_in_tank)
            if gallons_to_buy:
                purchases.append(FuelPurchase(current.station, gallons_to_buy, (gallons_to_buy * current.price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)))
                fuel_in_tank += gallons_to_buy
            fuel_in_tank -= self._gallons_between(current, next_node)
            index = nodes.index(next_node)
        return FuelPlan(purchases, sum((purchase.gallons for purchase in purchases), Decimal("0")), sum((purchase.cost for purchase in purchases), Decimal("0")))

    @staticmethod
    def _build_nodes(origin_station: StationCandidate, route_stations: list[StationCandidate], destination_mile: Decimal) -> list[_Node]:
        best_by_mile: dict[int, StationCandidate] = {}
        for station in route_stations:
            if station.station_id == origin_station.station_id or station.route_mile <= 0 or station.route_mile >= float(destination_mile):
                continue
            bucket = round(station.route_mile)
            if bucket not in best_by_mile or station.price < best_by_mile[bucket].price:
                best_by_mile[bucket] = station
        nodes = [_Node(origin_station, Decimal("0"))]
        nodes.extend(_Node(station, Decimal(str(station.route_mile))) for station in sorted(best_by_mile.values(), key=lambda station: station.route_mile))
        nodes.append(_Node(None, destination_mile))
        return nodes

    @staticmethod
    def _gallons_between(left: _Node, right: _Node) -> Decimal:
        return (right.route_mile - left.route_mile) / MPG

