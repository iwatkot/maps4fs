import os
import random

import config
import folium
import osmnx as ox


def get_preview(bboxes: list[tuple[float, float, float, float]]) -> str:
    save_path = get_save_path(bboxes)
    if os.path.isfile(save_path):
        return save_path

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

    m.save(save_path)
    return save_path


def get_random_color() -> str:
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def get_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    north, south, east, west = bbox
    return (north + south) / 2, (east + west) / 2


def get_bbox(center: tuple[float, float], size_meters: int) -> tuple[float, float, float, float]:
    center_lat, center_lon = center
    north, south, east, west = ox.utils_geo.bbox_from_point(
        (center_lat, center_lon), size_meters / 2, project_utm=False
    )
    return north, south, east, west


def get_save_path(bboxes: list[tuple[float, float, float, float]]) -> str:
    """Return the path to the HTML file where the OpenStreetMap data is saved.

    Arguments:
        lat (float): Latitude of the central point.
        lon (float): Longitude of the central point.
        size_meters (int): Width of the bounding box in meters.
        postfix (str): Optional postfix to add to the filename.

    Returns:
        str: Path to the HTML file.
    """
    file_names = [format_coordinates(bbox) for bbox in bboxes]
    filename = "_".join(file_names) + ".html"
    return os.path.join(
        config.OSMPS_DIRECTORY,
        filename,
    )


def format_coordinates(bbox: tuple[float, float, float, float]) -> str:
    """Return a string representation of the coordinates.

    Arguments:
        bbox (tuple[float, float, float, float]): The bounding box coordinates.

    Returns:
        str: String representation of the coordinates.
    """
    return "_".join(map(str, bbox))
