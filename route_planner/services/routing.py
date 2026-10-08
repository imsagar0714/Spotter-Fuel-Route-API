from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

from route_planner.services.exceptions import PlanningError
from route_planner.services.geo import Point

MILES_PER_METER = 0.000621371
CACHE_SECONDS = 60 * 60 * 24 * 30
USER_AGENT = "spotter-fuel-route-assessment/1.0 (educational-project)"


@dataclass(frozen=True)
class DrivingRoute:
    distance_miles: float
    duration_minutes: int
    geometry: list[Point]


class RoutingClient:
    """Adapter around Nominatim and OSRM, isolated for easy replacement and tests."""

    def geocode_us_location(self, query: str) -> Point:
        normalized_query = query.casefold().strip().encode("utf-8")
        cache_key = f"geocoding-us-{hashlib.sha256(normalized_query).hexdigest()}"
        if cached := cache.get(cache_key):
            return Point(**cached)
        response = self._get(f"{settings.NOMINATIM_BASE_URL}/search", {"q": query, "format": "jsonv2", "limit": "1", "countrycodes": "us", "addressdetails": "1"})
        matches: list[dict[str, Any]] = response.json()
        if not matches:
            raise PlanningError(f"Could not find a US location matching '{query}'.", 400)
        point = Point(float(matches[0]["lat"]), float(matches[0]["lon"]))
        if not self._is_us_point(point):
            raise PlanningError("Start and finish must both be within the United States.", 400)
        cache.set(cache_key, {"latitude": point.latitude, "longitude": point.longitude}, CACHE_SECONDS)
        return point

    def driving_route(self, start: Point, finish: Point) -> DrivingRoute:
        coordinates = f"{start.longitude},{start.latitude};{finish.longitude},{finish.latitude}"
        response = self._get(f"{settings.OSRM_BASE_URL}/route/v1/driving/{coordinates}", {"overview": "full", "geometries": "geojson", "steps": "false", "alternatives": "false"})
        payload = response.json()
        if payload.get("code") != "Ok" or not payload.get("routes"):
            raise PlanningError("A drivable route could not be found for these locations.")
        route = payload["routes"][0]
        return DrivingRoute(route["distance"] * MILES_PER_METER, round(route["duration"] / 60), [Point(latitude, longitude) for longitude, latitude in route["geometry"]["coordinates"]])

    @staticmethod
    def _is_us_point(point: Point) -> bool:
        continental = 24.3 <= point.latitude <= 49.5 and -125.1 <= point.longitude <= -66.7
        alaska = 51.2 <= point.latitude <= 71.5 and -179.2 <= point.longitude <= -129.8
        hawaii = 18.7 <= point.latitude <= 22.5 and -160.5 <= point.longitude <= -154.5
        return continental or alaska or hawaii

    @staticmethod
    def _get(url: str, params: dict[str, str]) -> requests.Response:
        try:
            response = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=settings.ROUTING_HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            raise PlanningError("The routing service is temporarily unavailable. Please try again.", 503) from error
