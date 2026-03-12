"""XmlDocument: fluent, safe wrapper around ElementTree for XML file manipulation."""

from __future__ import annotations

from xml.etree import ElementTree as ET


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
        # Capture original XML declaration so it is preserved verbatim on save.
        self._xml_declaration: str | None = None
        with open(path, "r", encoding="utf-8") as fh:
            first_line = fh.readline().rstrip("\n").rstrip("\r")
            if first_line.startswith("<?xml"):
                self._xml_declaration = first_line

    # ------------------------------------------------------------------
    # Static factory helpers (no parsed document required)
    # ------------------------------------------------------------------

    @staticmethod
    def create_element(tag: str, data: dict[str, str] | None = None) -> ET.Element:
        """Create a new detached XML element with optional attributes.

        Arguments:
            tag (str): The element tag name.
            data (dict[str, str] | None): Attributes to set on the element.

        Returns:
            ET.Element: The created element.
        """
        element = ET.Element(tag)
        if data:
            for key, value in data.items():
                element.set(key, value)
        return element

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

    def set_attrs(self, xpath: str, **attrs: str) -> XmlDocument:
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

    def remove_element(self, xpath: str) -> XmlDocument:
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
        """Write the tree back to the file it was loaded from.

        The output is pretty-printed with 2-space indentation.
        The original XML declaration (if any) is preserved verbatim so that
        quote style and encoding attributes remain unchanged.
        """
        ET.indent(self._tree, space="  ")
        if self._xml_declaration is not None:
            content = ET.tostring(self._root, encoding="unicode")
            with open(self._path, "w", encoding="utf-8") as fh:
                fh.write(self._xml_declaration + "\n")
                fh.write(content)
        else:
            self._tree.write(self._path, encoding="utf-8", xml_declaration=True)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> XmlDocument:
        return self

    def __exit__(self, *_) -> None:
        self.save()
