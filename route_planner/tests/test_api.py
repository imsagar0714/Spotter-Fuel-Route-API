from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient


class RoutePlanApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_rejects_matching_locations(self):
        response = self.client.post("/api/v1/route-plan/", {"start": "Chicago, IL", "finish": "chicago, il"}, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("route_planner.views.RoutePlanService")
    def test_returns_route_plan(self, service_class):
        service_class.return_value.build.return_value = {"summary": {"total_fuel_cost": 31.25}}
        response = self.client.post("/api/v1/route-plan/", {"start": "Dallas, TX", "finish": "Houston, TX"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["total_fuel_cost"], 31.25)

