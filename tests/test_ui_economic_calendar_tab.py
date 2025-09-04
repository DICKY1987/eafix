from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from ui_economic_calendar_tab import EconomicCalendarTab


def test_sections_present():
    tab = EconomicCalendarTab()
    for name in tab.section_names():
        assert hasattr(tab, name)
