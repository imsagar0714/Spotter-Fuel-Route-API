from decimal import Decimal

from django.test import SimpleTestCase

from route_planner.services.exceptions import PlanningError
from route_planner.services.geo import Point
from route_planner.services.optimizer import FuelOptimizer
from route_planner.services.stations import StationCandidate


def station(identifier, route_mile, price):
    return StationCandidate(
        identifier,
        f"Station {identifier}",
        "1 Main St",
        "Example",
        "TX",
        Decimal(price),
        Point(32, -96),
        route_mile,
        0,
    )


class FuelOptimizerTests(SimpleTestCase):

    def test_buys_only_enough_to_reach_cheaper_fuel(self):
        plan = FuelOptimizer().plan(
            station(1, 0, "4.00"),
            [
                station(2, 300, "3.00"),
                station(3, 500, "5.00"),
                station(4, 700, "2.00"),
            ],
            900,
        )

        self.assertEqual(
            [
                purchase.station.station_id
                for purchase in plan.purchases
            ],
            [1, 2, 4],
        )

        self.assertEqual(
            plan.total_gallons,
            Decimal("90"),
        )

        self.assertEqual(
            plan.total_cost,
            Decimal("280.00"),
        )

    def test_rejects_unreachable_gap(self):
        with self.assertRaises(PlanningError):
            FuelOptimizer().plan(
                station(1, 0, "3.00"),
                [],
                501,
            )

    def test_station_exactly_500_miles_is_reachable(self):
        plan = FuelOptimizer().plan(
            station(1, 0, "3.00"),
            [],
            500,
        )

        self.assertEqual(
            len(plan.purchases),
            1,
        )

        self.assertEqual(
            plan.purchases[0].gallons,
            Decimal("50"),
        )

        self.assertEqual(
            plan.purchases[0].cost,
            Decimal("150.00"),
        )

    def test_destination_reachable_buys_only_required_fuel(self):
        plan = FuelOptimizer().plan(
            station(1, 0, "3.00"),
            [],
            250,
        )

        self.assertEqual(
            plan.total_gallons,
            Decimal("25"),
        )

        self.assertEqual(
            plan.total_cost,
            Decimal("75.00"),
        )
    
    def test_uses_cheaper_reachable_station(self):
        plan = FuelOptimizer().plan(
            station(1, 0, "4.00"),
            [
                station(2, 200, "3.00"),
                station(3, 600, "5.00"),
            ],
            900,
        )

        self.assertEqual(
            [
                purchase.station.station_id
                for purchase in plan.purchases
            ],
            [1, 2, 3],
        )

        self.assertEqual(
            plan.purchases[0].gallons,
            Decimal("20"),
        )

        self.assertEqual(
            plan.purchases[1].gallons,
            Decimal("50"),
        )

    def test_fill_branch_caps_purchase_at_50_gallons(self):
        plan = FuelOptimizer().plan(
            station(1, 0, "3.00"),
            [
                station(2, 400, "4.00"),
                station(3, 700, "5.00"),
            ],
            900,
        )

        self.assertEqual(
            plan.purchases[0].gallons,
            Decimal("50"),
        )

        self.assertLessEqual(
            plan.purchases[0].gallons,
            Decimal("50"),
        )