import json
import urllib.request
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QFrame, QScrollArea
)

# WMO Weather interpretation codes (http://open-meteo.com/)
WEATHER_CODES = {
    0: ("Clear Sky", "☀️"),
    1: ("Mainly Clear", "🌤️"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Depositing Rime Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Moderate Drizzle", "🌦️"),
    55: ("Dense Drizzle", "🌧️"),
    61: ("Slight Rain", "🌦️"),
    63: ("Moderate Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    71: ("Slight Snow", "🌨️"),
    73: ("Moderate Snow", "❄️"),
    75: ("Heavy Snow", "❄️"),
    95: ("Thunderstorm", "⛈️")
}

CITIES = {
    "Gdańsk": (54.3520, 18.6466),
    "Warsaw": (52.2298, 21.0122),
    "London": (51.5085, -0.1257),
    "New York": (40.7143, -74.0060),
    "Tokyo": (35.6895, 139.6917)
}


class FetchWeatherThread(QThread):
    """Background worker to fetch live weather without freezing the Kiosk UI."""
    on_success = pyqtSignal(dict)
    on_error = pyqtSignal(str)

    def __init__(self, lat, lon):
        super().__init__()
        self.lat = lat
        self.lon = lon

    def run(self):
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.lat}&longitude={self.lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto"
        )
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Kiosk OS)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.on_success.emit(data)
        except Exception as e:
            self.on_error.emit(str(e))


class ForecastCard(QFrame):
    """A compact card displaying high/low temps for a single day."""
    def __init__(self, day_name, code, max_temp, min_temp):
        super().__init__()
        self.setFixedSize(130, 140)
        self.setStyleSheet("""
            ForecastCard {
                background-color: #1C1C22;
                border: 1px solid #2C2C35;
                border-radius: 14px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        lbl_day = QLabel(day_name)
        lbl_day.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_day.setStyleSheet("color: #AAAAAA; border: none;")

        _, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))
        lbl_icon = QLabel(emoji)
        lbl_icon.setFont(QFont("Arial", 28))
        lbl_icon.setStyleSheet("border: none;")

        lbl_temps = QLabel(f"{round(max_temp)}° / {round(min_temp)}°")
        lbl_temps.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        lbl_temps.setStyleSheet("color: white; border: none;")

        layout.addWidget(lbl_day, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_temps, alignment=Qt.AlignmentFlag.AlignCenter)


class WeatherPage(QWidget):
    """Standalone Live Weather Dashboard downloaded from GitHub App Store."""
    def __init__(self):
        super().__init__()
        self.current_city = "Gdańsk"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(15)

        # 1. Top Navigation & City Switcher
        nav_layout = QHBoxLayout()
        self.lbl_city_title = QLabel(self.current_city)
        self.lbl_city_title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.lbl_city_title.setStyleSheet("color: white;")
        nav_layout.addWidget(self.lbl_city_title)
        nav_layout.addStretch()

        self.city_buttons = []
        for city in CITIES.keys():
            btn = QPushButton(city)
            btn.setFixedSize(100, 40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=city: self.switch_city(c))
            nav_layout.addWidget(btn)
            self.city_buttons.append((city, btn))
        
        layout.addLayout(nav_layout)
        self.update_button_styles()

        # 2. Main Hero Section (Current Weather)
        hero_frame = QFrame()
        hero_frame.setFixedHeight(220)
        hero_frame.setStyleSheet("background-color: #16161A; border: 1px solid #282830; border-radius: 20px;")
        hero_layout = QHBoxLayout(hero_frame)
        hero_layout.setContentsMargins(40, 20, 40, 20)

        # Left Column: Temperature & Condition
        temp_layout = QVBoxLayout()
        self.lbl_temp = QLabel("--°C")
        self.lbl_temp.setFont(QFont("Arial", 64, QFont.Weight.Bold))
        self.lbl_temp.setStyleSheet("color: white; border: none;")
        
        self.lbl_condition = QLabel("Fetching weather data...")
        self.lbl_condition.setFont(QFont("Arial", 22))
        self.lbl_condition.setStyleSheet("color: #5A8DEF; border: none;")
        
        temp_layout.addWidget(self.lbl_temp)
        temp_layout.addWidget(self.lbl_condition)
        hero_layout.addLayout(temp_layout)
        hero_layout.addStretch()

        # Right Column: Humidity, Wind, Feels Like
        details_layout = QVBoxLayout()
        details_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        details_layout.setSpacing(12)
        
        self.lbl_feels = QLabel("Feels like: --°C")
        self.lbl_humidity = QLabel("💧 Humidity: --%")
        self.lbl_wind = QLabel("💨 Wind: -- km/h")
        
        for lbl in [self.lbl_feels, self.lbl_humidity, self.lbl_wind]:
            lbl.setFont(QFont("Arial", 16))
            lbl.setStyleSheet("color: #CCCCCC; border: none;")
            details_layout.addWidget(lbl)
            
        hero_layout.addLayout(details_layout)
        layout.addWidget(hero_frame)

        # 3. Forecast Section (Horizontal Scroll/Grid)
        lbl_forecast_title = QLabel("5-Day Forecast")
        lbl_forecast_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_forecast_title.setStyleSheet("color: #888888; margin-top: 5px;")
        layout.addWidget(lbl_forecast_title)

        self.forecast_container = QHBoxLayout()
        self.forecast_container.setSpacing(15)
        self.forecast_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(self.forecast_container)
        layout.addStretch()

        # Fetch initial city
        self.fetch_weather()

        # Auto-refresh every 30 minutes
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.fetch_weather)
        self.refresh_timer.start(30 * 60 * 1000)

    def switch_city(self, city_name):
        if city_name == self.current_city:
            return
        self.current_city = city_name
        self.lbl_city_title.setText(city_name)
        self.lbl_condition.setText("Updating...")
        self.update_button_styles()
        self.fetch_weather()

    def update_button_styles(self):
        for city, btn in self.city_buttons:
            if city == self.current_city:
                btn.setStyleSheet("background-color: #5A8DEF; color: white; font-weight: bold; border-radius: 8px; font-size: 14px;")
            else:
                btn.setStyleSheet("background-color: #22222A; color: #AAAAAA; border-radius: 8px; font-size: 14px;")

    def fetch_weather(self):
        lat, lon = CITIES[self.current_city]
        self.worker = FetchWeatherThread(lat, lon)
        self.worker.on_success.connect(self.update_ui)
        self.worker.on_error.connect(self.show_error)
        self.worker.start()

    def update_ui(self, data):
        current = data.get("current", {})
        daily = data.get("daily", {})

        # Update Current
        temp = current.get("temperature_2m", 0)
        feels = current.get("apparent_temperature", 0)
        hum = current.get("relative_humidity_2m", 0)
        wind = current.get("wind_speed_10m", 0)
        code = current.get("weather_code", 0)

        desc, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))
        
        self.lbl_temp.setText(f"{round(temp)}°C")
        self.lbl_condition.setText(f"{emoji}  {desc}")
        self.lbl_feels.setText(f"Feels like: {round(feels)}°C")
        self.lbl_humidity.setText(f"💧 Humidity: {hum}%")
        self.lbl_wind.setText(f"💨 Wind: {round(wind)} km/h")

        # Update Daily Forecast Cards
        for i in reversed(range(self.forecast_container.count())):
            self.forecast_container.itemAt(i).widget().setParent(None)

        days = ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5"]
        codes = daily.get("weather_code", [])
        maxs = daily.get("temperature_2m_max", [])
        mins = daily.get("temperature_2m_min", [])

        for i in range(min(5, len(codes))):
            card = ForecastCard(days[i], codes[i], maxs[i], mins[i])
            self.forecast_container.addWidget(card)

    def show_error(self, err_msg):
        self.lbl_condition.setText("Failed to update weather over network.")
        self.lbl_temp.setText("--°")
