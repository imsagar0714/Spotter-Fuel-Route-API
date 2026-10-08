# Spotter Fuel Route API

A Django REST API that plans a cost-aware fuel route between two US locations.

Given a start and destination, the API:

- Finds the locations and driving route.
- Returns the route as GeoJSON.
- Finds fuel stations along the route.
- Selects fuel stops based on fuel price and vehicle range.
- Calculates how much fuel to buy at each stop.
- Returns the estimated total fuel cost.

The project uses the fuel-price CSV provided with the assessment.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Setup](#setup)
- [API](#api)
- [Fuel Planning](#fuel-planning)
- [Fuel Station Data](#fuel-station-data)
- [Design Decisions and Tradeoffs](#design-decisions-and-tradeoffs)
- [Error Handling](#error-handling)
- [Tests](#tests)
- [Example Scenarios](#example-scenarios)
- [Future Improvements](#future-improvements)

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Language |
| Django 6.1 | Web framework |
| Django REST Framework | API layer |
| SQLite | Database |
| OSRM | Driving route calculation |
| Nominatim | Location geocoding |
| GeoNames | Approximate station coordinates |
| Postman | API testing |

---

## Project Structure

```text
Fuel_project/
├── config/
│   ├── settings.py
│   └── urls.py
│
├── data/
│   └── fuel-prices-for-be-assessment.csv
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
```

---

## How It Works

The API separates routing, station handling, and fuel optimization into different services.

```text
POST /api/v1/route-plan/
        |
        v
   API Serializer
        |
        v
  RoutePlanService
        |
        +----> Nominatim
        |       Location geocoding
        |
        +----> OSRM
        |       Driving route
        |
        +----> StationRepository
        |       Fuel station filtering
        |
        +----> FuelOptimizer
                Fuel planning
        |
        v
     JSON Response
```

The API view is kept relatively thin, while the main business logic is handled inside `route_planner/services/`. This makes the individual components easier to test and maintain.

---

## Setup

### Requirements

- Python 3.13
- Internet connection for Nominatim and OSRM
- GeoNames US dataset for the one-time station coordinate enrichment step

### 1. Create a virtual environment

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run migrations

```powershell
python manage.py migrate
```

### 4. Import the fuel-price data

```powershell
python manage.py import_fuel_prices --replace
```

### 5. Prepare station coordinates

The supplied fuel CSV does not contain latitude and longitude for the stations.

The project includes a one-time management command that matches stations with GeoNames US city coordinates.

Place the GeoNames US dataset at:

```text
data/geonames-us.zip
```

Then run:

```powershell
python manage.py enrich_station_coordinates
```

The GeoNames ZIP is intentionally excluded from Git because it is an external data artifact. It is only required when preparing station coordinates locally.

This step is performed before making API requests so that the application does not need to geocode thousands of stations for every route request.

### 6. Start the server

```powershell
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

---

## API

### Create Route Plan

**Endpoint**

```http
POST /api/v1/route-plan/
```

### Request

```json
{
    "start": "Dallas, TX",
    "finish": "Houston, TX"
}
```

### Example using cURL

```bash
curl -X POST http://127.0.0.1:8000/api/v1/route-plan/ \
  -H "Content-Type: application/json" \
  -d "{\"start\":\"Dallas, TX\",\"finish\":\"Houston, TX\"}"
```

---

## Response

The API returns:

- Start and destination coordinates
- Driving distance
- Estimated travel time
- Route geometry as GeoJSON
- Vehicle assumptions
- Selected fuel stops
- Fuel price at each stop
- Gallons purchased at each stop
- Cost at each stop
- Total fuel consumed
- Total estimated fuel cost

Example response:

```json
{
    "start": {
        "query": "Dallas, TX",
        "latitude": 32.7762719,
        "longitude": -96.7968559
    },
    "finish": {
        "query": "Houston, TX",
        "latitude": 29.7589382,
        "longitude": -95.3676974
    },
    "route": {
        "distance_miles": 238.41,
        "estimated_duration_minutes": 253,
        "geometry": {
            "type": "LineString",
            "coordinates": []
        }
    },
    "vehicle": {
        "fuel_efficiency_mpg": 10,
        "maximum_range_miles": 500,
        "tank_capacity_gallons": 50
    },
    "fuel_stops": [
        {
            "name": "CIRCLE K #2741192",
            "gallons_to_buy": 23.84,
            "cost": 69.11
        }
    ],
    "summary": {
        "total_fuel_gallons": 23.84,
        "total_fuel_cost": 69.11,
        "currency": "USD"
    }
}
```

The actual response contains the complete GeoJSON route coordinates returned by OSRM.

---

## Fuel Planning

The vehicle assumptions from the assessment are:

| Property | Value |
|---|---:|
| Fuel efficiency | 10 MPG |
| Tank capacity | 50 gallons |
| Maximum range | 500 miles |

The fuel planner uses a greedy, cost-aware strategy.

At each station, it considers the stations that can be reached within the vehicle's maximum range.

The logic is:

1. If the destination is reachable, buy only enough fuel to reach it.
2. Otherwise, if a cheaper reachable station exists, buy enough fuel to reach that station.
3. If there is no cheaper reachable station, fill the tank and continue towards the cheapest reachable station.
4. If no valid station can be reached within the maximum range, return a `422` response instead of producing an invalid fuel plan.

For this assessment, the vehicle starts empty. The first fuel stop is the closest supplied station within 35 miles of the starting location.

This assumption is also included in the API response.

---

## Fuel Station Data

The supplied CSV contains fuel station and price information but does not contain station coordinates.

To make the data usable for route calculations, the project uses the `enrich_station_coordinates` management command.

The command matches stations against GeoNames US city data and stores approximate coordinates.

During a route request, the application:

1. Loads the local station catalogue.
2. Finds stations close to the calculated route.
3. Calculates each candidate station's position along the route.
4. Passes the candidates to the fuel optimizer.

The current station search corridor is 25 miles from the route.

The response also includes `distance_from_route_miles` so that the approximation is visible to the API consumer.

---

## Design Decisions and Tradeoffs

### Station coordinates

The supplied fuel data does not contain exact GPS coordinates.

For this assessment, station addresses are matched to GeoNames US city coordinates as a practical approximation.

In production, I would use exact station coordinates and a spatial database such as PostGIS.

### Route and geocoding APIs

The project uses public Nominatim and OSRM services because they are free and suitable for demonstrating the solution.

For production, I would use providers with defined rate limits, SLAs, authentication, and monitoring.

### Pre-processing

Station coordinates are prepared once instead of being calculated during every request.

This avoids making thousands of external geocoding calls and keeps route requests faster.

### GeoJSON

The route is returned as a GeoJSON `LineString`, which makes it straightforward for a frontend or mapping library to display the calculated route.

---

## Error Handling

The API validates the request before starting the route-planning process.

Examples of invalid requests include:

- Missing start location
- Missing destination
- Start and destination being the same
- Location that cannot be geocoded
- No suitable starting fuel station
- No fuel station reachable within the vehicle's maximum range

If a valid fuel plan cannot be created, the API returns an appropriate error response instead of returning an incomplete plan.

---

## Tests

The project contains tests for the main parts of the application:

- API validation and responses
- Fuel optimization
- Fuel station filtering
- Route planning service
- Service integration

Run the complete test suite with:

```powershell
python manage.py test
```

The tests mock external routing/geocoding dependencies where appropriate, so the core application logic can be tested without relying on external services.

---

## Example Scenarios

### Dallas → Houston

A shorter route that demonstrates:

- Location geocoding
- Route calculation
- Fuel station selection
- Fuel calculation
- GeoJSON response

### Dallas → El Paso

A longer route that requires additional fuel planning because the distance exceeds the vehicle's 500-mile maximum range.

This scenario demonstrates the station selection and refueling logic more clearly.

---

## Future Improvements

For a production version, I would consider:

- Exact GPS coordinates for every fuel station
- PostGIS spatial queries and indexes
- Redis caching for route and geocoding responses
- A production routing/geocoding provider
- Automatic fuel-price updates
- Authentication and API rate limiting
- More advanced station and route scoring
- Frontend map visualization
- Docker-based deployment
- CI/CD
- Structured logging and monitoring
