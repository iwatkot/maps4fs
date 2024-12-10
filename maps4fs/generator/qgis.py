"""This module contains templates for generating QGIS scripts."""

import os

BBOX_TEMPLATE = """
layers = [
    {layers}
]
for layer in layers:
    name = "Bounding_Box_" + layer[0]
    north, south, east, west = layer[1:]

    # Create a rectangle geometry from the bounding box.
    rect = QgsRectangle(north, east, south, west)

    # Create a new memory layer to hold the bounding box.
    layer = QgsVectorLayer("Polygon?crs=EPSG:3857", name, "memory")
    provider = layer.dataProvider()

    # Add the rectangle as a feature to the layer.
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromRect(rect))
    provider.addFeatures([feature])

    # Add the layer to the map.
    QgsProject.instance().addMapLayer(layer)

    # Set the fill opacity.
    symbol = layer.renderer().symbol()
    symbol_layer = symbol.symbolLayer(0)

    # Set the stroke color and width.
    symbol_layer.setStrokeColor(QColor(0, 255, 0))
    symbol_layer.setStrokeWidth(0.2)
    symbol_layer.setFillColor(QColor(0, 0, 255, 0))
    layer.triggerRepaint()
"""

POINT_TEMPLATE = """
layers = [
    {layers}
]
for layer in layers:
    name = "Points_" + layer[0]
    north, south, east, west = layer[1:]

    top_left = QgsPointXY(north, west)
    top_right = QgsPointXY(north, east)
    bottom_right = QgsPointXY(south, east)
    bottom_left = QgsPointXY(south, west)

    points = [top_left, top_right, bottom_right, bottom_left, top_left]

    # Create a new layer
    layer = QgsVectorLayer('Point?crs=EPSG:3857', name, 'memory')
    provider = layer.dataProvider()

    # Add fields
    provider.addAttributes([QgsField("id", QVariant.Int)])
    layer.updateFields()

    # Create and add features for each point
    for i, point in enumerate(points):
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPointXY(point))
        feature.setAttributes([i + 1])
        provider.addFeature(feature)

    layer.updateExtents()

    # Add the layer to the project
    QgsProject.instance().addMapLayer(layer)
"""

RASTERIZE_TEMPLATE = """
import processing

############################################################
####### ADD THE DIRECTORY FOR THE FILES TO SAVE HERE #######
############################################################
############### IT MUST END WITH A SLASH (/) ###############
############################################################

SAVE_DIR = "C:/Users/iwatk/OneDrive/Desktop/"

############################################################

layers = [
    {layers}
]

for layer in layers:
    name = layer[0]
    north, south, east, west = layer[1:]

    epsg3857_string = str(north) + "," + str(south) + "," + str(east) + "," + str(west) + " [EPSG:3857]"
    file_path = SAVE_DIR + name + ".tif"

    processing.run(
        "native:rasterize",
        {{
            "EXTENT": epsg3857_string,
            "EXTENT_BUFFER": 0,
            "TILE_SIZE": 64,
            "MAP_UNITS_PER_PIXEL": 1,
            "MAKE_BACKGROUND_TRANSPARENT": False,
            "MAP_THEME": None,
            "LAYERS": None,
            "OUTPUT": file_path,
        }},
)
"""


def _get_template(layers: list[tuple[str, float, float, float, float]], template: str) -> str:
    """Returns a template for creating layers in QGIS.

    Arguments:
        layers (list[tuple[str, float, float, float, float]]): A list of tuples containing the
            layer name and the bounding box coordinates.
        template (str): The template for creating layers in QGIS.

    Returns:
        str: The template for creating layers in QGIS.
    """
    return template.format(
        layers=",\n    ".join(
            [
                f'("{name}", {north}, {south}, {east}, {west})'
                for name, north, south, east, west in layers
            ]
        )
    )


def get_bbox_template(layers: list[tuple[str, float, float, float, float]]) -> str:
    """Returns a template for creating bounding box layers in QGIS.

    Arguments:
        layers (list[tuple[str, float, float, float, float]]): A list of tuples containing the
            layer name and the bounding box coordinates.

    Returns:
        str: The template for creating bounding box layers in QGIS.
    """
    return _get_template(layers, BBOX_TEMPLATE)


def get_point_template(layers: list[tuple[str, float, float, float, float]]) -> str:
    """Returns a template for creating point layers in QGIS.

    Arguments:
        layers (list[tuple[str, float, float, float, float]]): A list of tuples containing the
            layer name and the bounding box coordinates.

    Returns:
        str: The template for creating point layers in QGIS.
    """
    return _get_template(layers, POINT_TEMPLATE)


def get_rasterize_template(layers: list[tuple[str, float, float, float, float]]) -> str:
    """Returns a template for rasterizing bounding box layers in QGIS.

    Arguments:
        layers (list[tuple[str, float, float, float, float]]): A list of tuples containing the
            layer name and the bounding box coordinates.

    Returns:
        str: The template for rasterizing bounding box layers in QGIS.
    """
    return _get_template(layers, RASTERIZE_TEMPLATE)


def save_scripts(
    layers: list[tuple[str, float, float, float, float]], file_prefix: str, save_directory: str
) -> None:
    """Saves QGIS scripts for creating bounding box, point, and raster layers.

    Arguments:
        layers (list[tuple[str, float, float, float, float]]): A list of tuples containing the
            layer name and the bounding box coordinates.
        save_dir (str): The directory to save the scripts.
    """
    script_files = [
        (f"{file_prefix}_bbox.py", get_bbox_template),
        (f"{file_prefix}_rasterize.py", get_rasterize_template),
        (f"{file_prefix}_point.py", get_point_template),
    ]

    for script_file, process_function in script_files:
        script_path = os.path.join(save_directory, script_file)
        script_content = process_function(layers)  # type: ignore

        with open(script_path, "w", encoding="utf-8") as file:
            file.write(script_content)
