import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from eafix.apps.desktop.ui_shell import STRENGTH_INDICATORS, create_central_widget


def test_strength_tab_present():
    app = QApplication.instance() or QApplication([])
    central = create_central_widget()
    tab_names = [central.tabText(i) for i in range(central.count())]
    assert "Strength" in tab_names
    strength_widget = central.widget(tab_names.index("Strength"))
    layout = strength_widget.layout()
    labels = [layout.itemAt(i).widget().text() for i in range(layout.count())]
    for name in STRENGTH_INDICATORS:
        assert name in labels
    app.quit()

