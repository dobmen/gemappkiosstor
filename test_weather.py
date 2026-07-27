import sys
from unittest.mock import MagicMock
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()

import apps.weather as w
print("Imported successfully")

try:
    page = w.WeatherPage()
    print("Instantiated successfully")
except Exception as e:
    print("Exception during init:", e)
