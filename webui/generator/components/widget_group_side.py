from generator.components.widget_group import WidgetGroup
from generator.components.widgets.widgets_side import EnableDebug, SideTitleWidget


class SideWidgetGroup(WidgetGroup):
    _widgets = [SideTitleWidget, EnableDebug]
