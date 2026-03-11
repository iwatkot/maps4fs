"""Geographic lookup utilities — country/region detection from coordinates."""

from __future__ import annotations

from typing import Literal

from geopy.geocoders import Nominatim


def get_country_by_coordinates(coordinates: tuple[float, float]) -> str:
    """Return the country name for the given (latitude, longitude) pair.

    Arguments:
        coordinates (tuple[float, float]): (latitude, longitude).

    Returns:
        str: Country name, or "Unknown" on any error.
    """
    try:
        geolocator = Nominatim(user_agent="maps4fs")
        location = geolocator.reverse(coordinates, language="en")
        if location and "country" in location.raw["address"]:
            return location.raw["address"]["country"]
    except Exception:
        return "Unknown"
    return "Unknown"


def get_region_by_coordinates(coordinates: tuple[float, float]) -> Literal["EU", "US"]:
    """Return "EU" or "US" based on the country at the given coordinates.

    Arguments:
        coordinates (tuple[float, float]): (latitude, longitude).

    Returns:
        Literal["EU", "US"]: "US" if the country is the United States, "EU" otherwise.
    """
    country = get_country_by_coordinates(coordinates)
    return "US" if country == "United States" else "EU"
