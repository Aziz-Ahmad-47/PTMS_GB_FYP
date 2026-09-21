import requests


OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def get_route(start_lat, start_lon, end_lat, end_lon):

    url = (
        f"{OSRM_URL}/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        return None

    routes = data.get("routes", [])

    if not routes:
        return None

    route = routes[0]

    return {
        "distance_km": route["distance"] / 1000,
        "duration_hours": route["duration"] / 3600,
        "geometry": route["geometry"]
    }