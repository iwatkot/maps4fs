"""This module contains templates for generating QGIS scripts."""

BBOX_TEMPLATE = """
layers = [
    {layers}
]
for layer in layers:
    name = layer[0]
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


def get_bbox_template(layers: list[tuple[str, float, float, float, float]]) -> str:
    """Returns a template for creating bounding box layers in QGIS.

    Args:
        layers (list[tuple[str, float, float, float, float]]): A list of tuples containing the
            layer name and the bounding box coordinates.

    Returns:
        str: The template for creating bounding box layers in QGIS.
    """
    return BBOX_TEMPLATE.format(
        layers=",\n    ".join(
            [
                f'("{name}", {north}, {south}, {east}, {west})'
                for name, north, south, east, west in layers
            ]
        )
    )


def get_rasterize_template(layers: list[tuple[str, float, float, float, float]]) -> str:
    """Returns a template for rasterizing bounding box layers in QGIS.

    Args:
        layers (list[tuple[str, float, float, float, float]]): A list of tuples containing the
            layer name and the bounding box coordinates.

    Returns:
        str: The template for rasterizing bounding box layers in QGIS.
    """
    return RASTERIZE_TEMPLATE.format(
        layers=",\n    ".join(
            [
                f'("{name}", {north}, {south}, {east}, {west})'
                for name, north, south, east, west in layers
            ]
        )
    )
