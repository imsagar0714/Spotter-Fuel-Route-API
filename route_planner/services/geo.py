from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Iterable

EARTH_RADIUS_MILES = 3958.7613


@dataclass(frozen=True)
class Point:
    latitude: float
    longitude: float


def haversine_miles(left: Point, right: Point) -> float:
    latitude_delta = radians(right.latitude - left.latitude)
    longitude_delta = radians(right.longitude - left.longitude)
    value = sin(latitude_delta / 2) ** 2 + cos(radians(left.latitude)) * cos(radians(right.latitude)) * sin(longitude_delta / 2) ** 2
    return EARTH_RADIUS_MILES * 2 * asin(sqrt(value))


def sampled_route(points: list[Point], sample_count: int = 160) -> list[tuple[Point, float]]:
    if len(points) < 2:
        return [(point, 0.0) for point in points]
    segment_lengths = [haversine_miles(points[index], points[index + 1]) for index in range(len(points) - 1)]
    total_miles = sum(segment_lengths)
    if total_miles == 0:
        return [(points[0], 0.0)]
    result: list[tuple[Point, float]] = []
    segment_index = 0
    miles_before_segment = 0.0
    for index in range(sample_count):
        target_mile = total_miles * index / (sample_count - 1)
        while segment_index < len(segment_lengths) - 1 and miles_before_segment + segment_lengths[segment_index] < target_mile:
            miles_before_segment += segment_lengths[segment_index]
            segment_index += 1
        segment_length = segment_lengths[segment_index]
        fraction = (target_mile - miles_before_segment) / segment_length if segment_length else 0
        start, end = points[segment_index], points[segment_index + 1]
        result.append((Point(start.latitude + (end.latitude - start.latitude) * fraction, start.longitude + (end.longitude - start.longitude) * fraction), target_mile))
    return result


def bounds(points: Iterable[Point], buffer_degrees: float = 0.5) -> tuple[float, float, float, float]:
    points = list(points)
    return (min(point.latitude for point in points) - buffer_degrees, max(point.latitude for point in points) + buffer_degrees, min(point.longitude for point in points) - buffer_degrees, max(point.longitude for point in points) + buffer_degrees)

