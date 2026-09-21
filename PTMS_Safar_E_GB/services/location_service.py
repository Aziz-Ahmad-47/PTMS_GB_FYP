import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"


def get_coordinates(place):

    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "AI-TravelMate/1.2"
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    return {
        "name": data[0].get("display_name", place),
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"])
    }


def get_elevation(latitude, longitude):

    params = {
        "latitude": latitude,
        "longitude": longitude
    }

    response = requests.get(
        ELEVATION_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    elevations = data.get("elevation", [])

    if not elevations:
        return None

    return elevations[0]