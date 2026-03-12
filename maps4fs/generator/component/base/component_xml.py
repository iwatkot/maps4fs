"""Base class for all components that primarily used to work with XML files."""

from xml.etree import ElementTree as ET

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.settings import Parameters


class XMLComponent(Component):
    """Base class for all components that primarily used to work with XML files."""

    xml_path: str | None = None

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
        doc = XmlDocument(self.game.i3d_file_path)
        height_scale_element = doc.get(".//Scene/TerrainTransformGroup")
        if height_scale_element is None:
            raise ValueError("Height scale element not found in the I3D file.")

        height_scale = height_scale_element.get(Parameters.HEIGHT_SCALE)
        if height_scale is None:
            raise ValueError("Height scale not found in the I3D file.")

        return int(height_scale)


class XmlDocument:
    """Fluent, safe wrapper around ElementTree.

    Replaces direct ET.parse / getroot / find / findall / write usage.
    Use as a context manager to auto-save on exit::

        with XmlDocument(path) as doc:
            doc.set_attrs(".//Scene/Terrain", heightScale="255")

    Or manage persistence manually::

        doc = XmlDocument(path)
        doc.set_attrs(...)
        doc.save()
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._tree = ET.parse(path)
        self._root = self._tree.getroot()

    # ------------------------------------------------------------------
    # Root access (for callers that need raw ET.Element manipulation)
    # ------------------------------------------------------------------

    @property
    def root(self) -> ET.Element:
        return self._root

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get(self, xpath: str) -> ET.Element | None:
        """Return the first element matching *xpath*, or None."""
        return self._root.find(xpath)

    def require(self, xpath: str) -> ET.Element:
        """Return the first element matching *xpath*.

        Raises:
            ValueError: If no element is found.
        """
        element = self._root.find(xpath)
        if element is None:
            raise ValueError(f"Required XML element not found: {xpath!r}")
        return element

    def find_all(self, xpath: str) -> list[ET.Element]:
        """Return all elements matching *xpath*."""
        return self._root.findall(xpath)

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def set_attrs(self, xpath: str, **attrs: str) -> "XmlDocument":
        """Set attributes on the element at *xpath*. Fluent — returns self.

        Raises:
            ValueError: If the element is not found.
        """
        elem = self.require(xpath)
        for key, value in attrs.items():
            elem.set(key, value)
        return self

    def append_child(self, xpath: str, tag: str, **attrs: str) -> ET.Element:
        """Append a new child element under the element at *xpath*.

        Returns:
            ET.Element: The newly created child element.
        """
        parent = self.require(xpath)
        child = ET.SubElement(parent, tag)
        for key, value in attrs.items():
            child.set(key, value)
        return child

    def remove_element(self, xpath: str) -> "XmlDocument":
        """Remove all elements matching *xpath* from their parents. Fluent."""
        for elem in self._root.findall(xpath):
            parent_xpath = xpath.rsplit("/", 1)[0] or "."
            parent = self._root.find(parent_xpath)
            if parent is not None:
                parent.remove(elem)
        return self

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Write the tree back to the file it was loaded from."""
        self._tree.write(self._path, encoding="utf-8", xml_declaration=True)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "XmlDocument":
        return self

    def __exit__(self, *_) -> None:
        self.save()
