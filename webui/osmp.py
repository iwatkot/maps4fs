import os

import config
import folium
import osmnx as ox


def get_preview(center_lat: float, center_lon: float, size_meters: int) -> str:
    """Generate an HTML file with OpenStreetMap data centered at the given point and size in meters.

    Arguments:
        center_lat (float): Latitude of the central point.
        center_lon (float): Longitude of the central point.
        size_meters (int): Width of the bounding box in meters.
        output_file (str): Path to the output HTML file.

    Returns:
        str: Path to the HTML file where the OpenStreetMap data is saved.
    """
    save_path = get_save_path(center_lat, center_lon, size_meters)
    if os.path.isfile(save_path):
        return save_path
    # Calculate the bounding box
    center = (center_lat, center_lon)

    north, south, east, west = ox.utils_geo.bbox_from_point(
        center, size_meters / 2, project_utm=False
    )

    # Create a map centered at the given point
    m = folium.Map(location=[center_lat, center_lon], max_bounds=True)

    # Draw the bounding box
    folium.Rectangle(
        bounds=[[south, west], [north, east]], color="blue", fill=True, fill_opacity=0.2
    ).add_to(m)

    m.fit_bounds([[south, west], [north, east]])

    # Save the map as an HTML file
    m.save(save_path)
    return save_path


def get_save_path(lat: float, lon: float, size_meters: int) -> str:
    """Return the path to the HTML file where the OpenStreetMap data is saved.

    Arguments:
        lat (float): Latitude of the central point.
        lon (float): Longitude of the central point.
        size_meters (int): Width of the bounding box in meters.

    Returns:
        str: Path to the HTML file.
    """
    return os.path.join(
        config.OSMPS_DIRECTORY,
        f"{format_coordinates(lat, lon)}_{size_meters}.html",
    )


def format_coordinates(lat: float, lon: float) -> str:
    """Return a string representation of the coordinates.

    Arguments:
        lat (float): Latitude.
        lon (float): Longitude.

    Returns:
        str: String representation of the coordinates.
    """
    return f"{lat:.6f}_{lon:.6f}"
