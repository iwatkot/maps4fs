from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from generator.generator import GeneratorUI
else:
    GeneratorUI = object


class Widget:
    def __init__(self, ui: GeneratorUI):
        self._ui = ui
        self.content()

    @property
    def ui(self) -> GeneratorUI:
        return self._ui

    def content(self) -> None:
        raise NotImplementedError
