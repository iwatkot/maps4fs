import math
import random
from typing import NamedTuple

import folium
import osmnx as ox


class MapEntry(NamedTuple):
    """Represents a map entry."""

    latitude: float
    longitude: float
    size: int
    rotation: int


def get_rotated_previews(
    entries: list[MapEntry],
    add_markers: bool = False,
    add_bboxes: bool = True,
) -> folium.Map:
    """Return the path to the HTML file where the OpenStreetMap data is saved.

    Arguments:
        entries (list[MapEntry]): List of map entries.
        add_markers (bool): True if the center markers should be added, False otherwise.
        add_bboxes (bool): True if the bounding boxes should be added, False otherwise.

    Returns:
        folium.Map: Folium map object.
    """
    m = folium.Map(zoom_control=False)

    if not add_markers and not add_bboxes:
        raise ValueError("At least one of add_markers or add_bboxes must be True.")

    for entry in entries:
        get_rotated_preview(
            entry.latitude,
            entry.longitude,
            entry.size,
            entry.rotation,
            map=m,
            color="#50b0c3",
            fit_bounds=False,
            add_tile_layer=False,
            add_center_marker=add_markers,
            add_center_marker_as_pin=True,
            add_click_for_marker=False,
            add_bbox=add_bboxes,
        )

    return m


def get_rotated_preview(
    lat: float,
    lon: float,
    distance: int,
    angle: int,
    map: folium.Map | None = None,
    add_tile_layer: bool = True,
    color: str | None = None,
    fit_bounds: bool = True,
    add_center_marker: bool = True,
    add_center_marker_as_pin: bool = False,
    add_click_for_marker: bool = True,
    add_bbox: bool = True,
) -> folium.Map:
    """Return the path to the HTML file where the OpenStreetMap data is saved.

    Arguments:
        lat (float): Latitude of the central point.
        lon (float): Longitude of the central point.
        distance (int): Width of the bounding box in meters.
        angle (int): Angle of rotation in degrees.
        map (folium.Map | None): Folium map object to add the square polygon to.
            If not provided, a new map object will be created.
        add_tile_layer (bool): True if the tile layer should be added, False otherwise.
        color (str | None): Color of the square polygon.
        fit_bounds (bool): True if the map should be fitted to the bounding box, False otherwise.
        add_center_marker (bool): True if the center marker should be added, False otherwise.
        add_click_for_marker (bool): True if the click for marker should be added, False otherwise.
        add_bbox (bool): True if the bounding box should be added, False otherwise.

    Returns:
        folium.Map: Folium map object.
    """
    m = map or folium.Map(zoom_control=False)
    color = color or get_random_color()

    if add_tile_layer:
        url = "https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga"
        folium.TileLayer(
            tiles=url, name="satellite", attr="Google", overlay=True, show=False, control=True
        ).add_to(m)
        folium.LayerControl().add_to(m)

    if add_bbox:
        corners = []
        half_diagonal = distance * math.sqrt(2) / 2  # Half the diagonal length of the square
        for i in range(4):
            theta = math.radians(angle + i * 90 + 45)  # Rotate by 45 degrees to get the corners
            dx = half_diagonal * math.cos(theta)
            dy = half_diagonal * math.sin(theta)
            corner_lat = lat + (
                dy / 111320
            )  # Approximate conversion from meters to degrees latitude
            corner_lon = lon + (
                dx / (111320 * math.cos(math.radians(lat)))
            )  # Approximate conversion from meters to degrees longitude
            corners.append((corner_lat, corner_lon))

        folium.Polygon(
            locations=corners, color=color, fill=True, fill_opacity=0.1, fill_color=color
        ).add_to(m)

    bbox = get_bbox((lat, lon), distance)
    north, south, east, west = bbox

    if fit_bounds:
        m.fit_bounds([[south, west], [north, east]])

    if add_click_for_marker:
        folium.ClickForMarker("<b>${lat}, ${lng}</b>").add_to(m)

    if add_center_marker:
        center = get_center(bbox)
        if not add_center_marker_as_pin:
            folium.CircleMarker(center, radius=1, color=color, fill=True).add_to(m)
        else:
            short_lat_lon = f"{round(lat, 4)}, {round(lon, 4)}"
            folium.Marker(
                center,
                popup=f"<b>Coordinates:</b> {short_lat_lon}\n<b>Size:</b> {distance} m\n<b>Rotation:</b> {angle}°",
            ).add_to(m)

    return m


def get_preview(bboxes: list[tuple[float, float, float, float]]) -> folium.Map:
    """Returns the folium map object with the bounding boxes.

    Arguments:
        bboxes (list[tuple[float, float, float, float]]): List of bounding boxes.

    Returns:
        folium.Map: Folium map object.
    """
    m = folium.Map(zoom_control=False)

    for bbox in bboxes:
        center = get_center(bbox)
        north, south, east, west = bbox
        color = get_random_color()
        folium.CircleMarker(center, radius=1, color=color, fill=True).add_to(m)

        folium.Rectangle(
            bounds=[[south, west], [north, east]],
            color=color,
            fill=True,
            fill_opacity=0.1,
            fill_color=color,
        ).add_to(m)

    folium.ClickForMarker("<b>${lat}, ${lng}</b>").add_to(m)

    # Fit bounds to the last bbox in the list.
    m.fit_bounds([[south, west], [north, east]])

    return m


def get_random_color() -> str:
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def get_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    north, south, east, west = bbox
    return (north + south) / 2, (east + west) / 2


def get_bbox(center: tuple[float, float], size_meters: int) -> tuple[float, float, float, float]:
    center_lat, center_lon = center
    west, south, east, north = ox.utils_geo.bbox_from_point(
        (center_lat, center_lon), size_meters / 2, project_utm=False
    )
    return north, south, east, west
