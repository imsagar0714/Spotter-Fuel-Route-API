# Spotter Fuel Route API

A Django REST API that plans a fuel-efficient driving route between two US locations.

Given a start and destination, the API:

- Finds the locations and driving route.
- Returns the route as GeoJSON.
- Finds fuel stations along the route.
- Selects fuel stops based on fuel price and vehicle range.
- Calculates how much fuel to buy at each stop.
- Returns the estimated total fuel cost.

The project uses the fuel-price CSV provided with the assessment.

---

## Tech Stack

- Python 3.13
- Django 6.1
- Django REST Framework
- SQLite
- OSRM - driving route calculation
- Nominatim - location geocoding
- GeoNames - approximate station coordinates
- Postman - API testing

---

## Project Structure

```text
Fuel_project/
├── config/
│   ├── settings.py
│   └── urls.py
│
├── data/
│   ├── fuel-prices-for-be-assessment.csv
│   └── geonames-us.zip
│
├── route_planner/
│   ├── management/
│   │   └── commands/
│   │       ├── import_fuel_prices.py
│   │       └── enrich_station_coordinates.py
│   │
│   ├── services/
│   │   ├── geo.py
│   │   ├── routing.py
│   │   ├── stations.py
│   │   ├── optimizer.py
│   │   ├── planner.py
│   │   └── exceptions.py
│   │
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_optimizer.py
│   │   ├── test_stations.py
│   │   └── test_planner.py
│   │
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── manage.py
├── requirements.txt
└── README.md