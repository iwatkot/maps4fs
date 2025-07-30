"""Base class for all components that primarily used to work with XML files."""

import os
from xml.etree import ElementTree as ET

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.settings import Parameters


class XMLComponent(Component):
    """Base class for all components that primarily used to work with XML files."""

    xml_path: str | None = None

    def get_tree(self, xml_path: str | None = None) -> ET.ElementTree:
        """Parses the XML file and returns the tree.
        If the XML path is not provided, the class attribute is used.

        Arguments:
            xml_path (str, optional): The path to the XML file. Defaults to None.

        Raises:
            ValueError: If the XML path is not set as a class attribute nor provided as an
                argument.
            FileNotFoundError: If the XML file does not exist

        Returns:
            ET.ElementTree: The parsed XML tree.
        """
        xml_path = xml_path or self.xml_path
        if not xml_path:
            raise ValueError(
                "XML path was not set as a class attribute nor provided as an argument."
            )

        if not os.path.isfile(xml_path):
            raise FileNotFoundError(f"XML file {xml_path} does not exist.")

        return ET.parse(xml_path)  # type: ignore

    def save_tree(self, tree: ET.ElementTree, xml_path: str | None = None) -> None:
        """Saves the XML tree to the file.
        If the XML path is not provided, the class attribute is used.

        Arguments:
            tree (ET.ElementTree): The XML tree to save.
            xml_path (str, optional): The path to the XML file. Defaults to None.

        Raises:
            ValueError: If the XML path is not set as a class attribute nor provided as an
                argument.
        """
        xml_path = xml_path or self.xml_path
        if not xml_path:
            raise ValueError(
                "XML path was not set as a class attribute nor provided as an argument."
            )

        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    def get_element_from_tree(self, path: str, xml_path: str | None = None) -> ET.Element | None:
        """Finds an element in the XML tree by the path.

        Arguments:
            path (str): The path to the element.
            xml_path (str, optional): The path to the XML file. Defaults to None.

        Returns:
            ET.Element | None: The found element or None if not found.
        """
        tree = self.get_tree(xml_path)
        root = tree.getroot()
        return root.find(path)  # type: ignore

    def get_and_update_element(self, root: ET.Element, path: str, data: dict[str, str]) -> None:
        """Finds the element by the path and updates it with the provided data.

        Arguments:
            root (ET.Element): The root element of the XML tree.
            path (str): The path to the element.
            data (dict[str, str]): The data to update the element with.
        """
        element = root.find(path)
        if element is not None:
            self.update_element(element, data)

    def update_element(self, element: ET.Element, data: dict[str, str]) -> None:
        """Updates the element with the provided data.

        Arguments:
            element (ET.Element): The element to update.
            data (dict[str, str]): The data to update the element with.
        """
        for key, value in data.items():
            element.set(key, value)

    def create_element(self, element_name: str, data: dict[str, str]) -> ET.Element:
        """Creates an element with the provided data.

        Arguments:
            element_name (str): The name of the element.
            data (dict[str, str]): The data to set the element attributes to.

        Returns:
            ET.Element: The created element.
        """
        element = ET.Element(element_name)
        for key, value in data.items():
            element.set(key, value)
        return element

    def create_subelement(
        self, parent: ET.Element, element_name: str, data: dict[str, str]
    ) -> None:
        """Creates a subelement under the parent element with the provided data.

        Arguments:
            parent (ET.Element): The parent element.
            element_name (str): The name of the subelement.
            data (dict[str, str]): The data to set the subelement attributes to.
        """
        element = ET.SubElement(parent, element_name)
        self.update_element(element, data)

    def get_height_scale(self) -> int:
        """Returns the height scale from the I3D file.

        Returns:
            int: The height scale value.

        Raises:
            ValueError: If the height scale element is not found in the I3D file.
        """
        height_scale_element = self.get_element_from_tree(
            path=".//Scene/TerrainTransformGroup",
            xml_path=self.game.i3d_file_path(self.map_directory),
        )
        if height_scale_element is None:
            raise ValueError("Height scale element not found in the I3D file.")

        height_scale = height_scale_element.get(Parameters.HEIGHT_SCALE)
        if height_scale is None:
            raise ValueError("Height scale not found in the I3D file.")

        return int(height_scale)
