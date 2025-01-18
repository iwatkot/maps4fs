from __future__ import annotations

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from generator.generator import GeneratorUI

    from webui.generator.components.widgets.widget import Widget


class WidgetGroup:
    _widgets: list[Type[Widget]]

    def __init__(self, ui: GeneratorUI):
        self._ui = ui
        self.show()

    @property
    def ui(self) -> GeneratorUI:
        return self._ui

    @property
    def widgets(self) -> list[Widget]:
        return self._widgets

    def show(self) -> None:
        for widget in self.widgets:
            widget(self.ui)


class InputWidgetGroup(WidgetGroup):
    pass


class OutputWidgetGroup(WidgetGroup):
    pass
