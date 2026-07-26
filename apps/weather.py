import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QGuiApplication, QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QFrame, QScrollArea, QLineEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QSizePolicy
)

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
    80: ("Rain Showers", "🌦️"),
    81: ("Heavy Showers", "🌧️"),
    82: ("Violent Showers", "⛈️"),
    95: ("Thunderstorm", "⛈️")
}

CONFIG_FILE = os.path.expanduser("~/.kiosk_weather_locs.json")

def get_scale_factor():
    screen = QGuiApplication.primaryScreen()
    return max(1.0, screen.size().width() / 1024.0) if screen else 1.0


class GeocodeThread(QThread):
    on_success = pyqtSignal(list)
    on_error = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        encoded = urllib.parse.quote(self.query)
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=5&language=en&format=json"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.on_success.emit(data.get("results", []))
        except Exception as e:
            self.on_error.emit(str(e))


class FetchWeatherThread(QThread):
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
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,is_day,visibility&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max&timezone=auto"
        )
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.on_success.emit(data)
        except Exception as e:
            self.on_error.emit(str(e))


class GlassCard(QFrame):
    def __init__(self, title, icon, value="--"):
        super().__init__()
        self.scale = get_scale_factor()
        self.setStyleSheet("""
            GlassCard {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(int(15*self.scale), int(15*self.scale), int(15*self.scale), int(15*self.scale))
        
        header = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setFont(QFont("Google Sans", int(14*self.scale)))
        lbl_icon.setStyleSheet("color: rgba(255,255,255,180); background: transparent; border: none;")
        
        lbl_title = QLabel(title.upper())
        lbl_title.setFont(QFont("Google Sans", int(12*self.scale), QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: rgba(255,255,255,180); background: transparent; border: none;")
        
        header.addWidget(lbl_icon)
        header.addWidget(lbl_title)
        header.addStretch()
        layout.addLayout(header)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(QFont("Google Sans", int(24*self.scale), QFont.Weight.Bold))
        self.lbl_value.setStyleSheet("color: white; background: transparent; border: none;")
        self.lbl_value.setWordWrap(True)
        layout.addWidget(self.lbl_value)
        layout.addStretch()

    def set_value(self, val):
        self.lbl_value.setText(str(val))


class ForecastCard(QFrame):
    def __init__(self, day_name, code, max_temp, min_temp):
        super().__init__()
        self.scale = get_scale_factor()
        self.setFixedSize(int(130 * self.scale), int(140 * self.scale))
        self.setStyleSheet("""
            ForecastCard {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(int(6 * self.scale))

        lbl_day = QLabel(day_name)
        lbl_day.setFont(QFont("Google Sans", int(14 * self.scale), QFont.Weight.Bold))
        lbl_day.setStyleSheet("color: white; background: transparent; border: none;")

        _, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))
        lbl_icon = QLabel(emoji)
        lbl_icon.setFont(QFont("Google Sans", int(28 * self.scale)))
        lbl_icon.setStyleSheet("background: transparent; border: none;")

        lbl_temps = QLabel(f"{round(max_temp)}° / {round(min_temp)}°")
        lbl_temps.setFont(QFont("Google Sans", int(15 * self.scale), QFont.Weight.Bold))
        lbl_temps.setStyleSheet("color: white; background: transparent; border: none;")

        layout.addWidget(lbl_day, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_temps, alignment=Qt.AlignmentFlag.AlignCenter)


class GradientBackground(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#1A4D8B"))
        grad.setColorAt(1.0, QColor("#4A90E2"))
        painter.fillRect(self.rect(), grad)


class AddLocationScreen(GradientBackground):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.scale = get_scale_factor()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(int(40*self.scale), int(60*self.scale), int(40*self.scale), int(40*self.scale))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        top_layout = QHBoxLayout()
        lbl_title = QLabel("Add Location")
        lbl_title.setFont(QFont("Google Sans", int(32*self.scale), QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: white; background: transparent;")
        top_layout.addWidget(lbl_title)
        
        if self.main_app.locations:
            btn_cancel = QPushButton("Cancel")
            btn_cancel.setFixedSize(int(100*self.scale), int(40*self.scale))
            btn_cancel.setStyleSheet(f"background-color: rgba(255,255,255,40); color: white; border-radius: {int(20*self.scale)}px; font-weight: bold; border: none;")
            btn_cancel.clicked.connect(lambda: self.main_app.switch_to_main())
            top_layout.addStretch()
            top_layout.addWidget(btn_cancel)
            
        layout.addLayout(top_layout)
        layout.addSpacing(int(20*self.scale))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for a city...")
        self.search_input.setFixedHeight(int(60*self.scale))
        self.search_input.setFont(QFont("Google Sans", int(18*self.scale)))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255,255,255,200);
                color: black;
                border-radius: {int(15*self.scale)}px;
                padding: 0 {int(20*self.scale)}px;
                border: none;
            }}
        """)
        self.search_input.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.search_input)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: rgba(0,0,0,50);
                border-radius: {int(15*self.scale)}px;
                border: none;
            }}
            QListWidget::item {{
                color: white;
                padding: {int(15*self.scale)}px;
                border-bottom: 1px solid rgba(255,255,255,20);
            }}
            QListWidget::item:selected {{
                background-color: rgba(255,255,255,40);
            }}
        """)
        self.results_list.setFont(QFont("Google Sans", int(16*self.scale)))
        self.results_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.results_list)
        
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.perform_search)
        
        self.current_results = []
        self.worker = None

    def on_text_changed(self):
        self.debounce_timer.start(400)
        
    def perform_search(self):
        query = self.search_input.text().strip()
        if len(query) < 2:
            self.results_list.clear()
            return
            
        if self.worker:
            self.worker.terminate()
            
        self.worker = GeocodeThread(query)
        self.worker.on_success.connect(self.populate_results)
        self.worker.start()
        
    def populate_results(self, results):
        self.results_list.clear()
        self.current_results = results
        for r in results:
            name = r.get("name", "Unknown")
            admin = r.get("admin1", "")
            country = r.get("country", "")
            display = f"{name}"
            if admin: display += f", {admin}"
            if country: display += f", {country}"
            self.results_list.addItem(display)
            
    def on_item_clicked(self, item):
        idx = self.results_list.row(item)
        if 0 <= idx < len(self.current_results):
            data = self.current_results[idx]
            loc = {
                "name": data.get("name"),
                "lat": data.get("latitude"),
                "lon": data.get("longitude")
            }
            self.main_app.add_location(loc)


class MainWeatherScreen(GradientBackground):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.scale = get_scale_factor()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(int(20*self.scale), int(20*self.scale), int(20*self.scale), int(20*self.scale))
        
        # --- Top Nav ---
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setFixedHeight(int(70*self.scale))
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.nav_container = QWidget()
        self.nav_container.setStyleSheet("background: transparent;")
        self.nav_layout = QHBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.nav_scroll.setWidget(self.nav_container)
        self.layout.addWidget(self.nav_scroll)
        
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.c_layout = QVBoxLayout(content)
        self.c_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.c_layout.setContentsMargins(int(40*self.scale), int(10*self.scale), int(40*self.scale), int(40*self.scale))
        self.c_layout.setSpacing(int(20*self.scale))
        
        # --- Hero Section ---
        self.lbl_city = QLabel("City")
        self.lbl_city.setFont(QFont("Google Sans", int(42*self.scale), QFont.Weight.Medium))
        self.lbl_city.setStyleSheet("color: white; background: transparent;")
        self.lbl_city.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_temp = QLabel("--°")
        self.lbl_temp.setFont(QFont("Google Sans", int(96*self.scale), QFont.Weight.Thin))
        self.lbl_temp.setStyleSheet("color: white; background: transparent;")
        self.lbl_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_cond = QLabel("Loading...")
        self.lbl_cond.setFont(QFont("Google Sans", int(24*self.scale), QFont.Weight.Medium))
        self.lbl_cond.setStyleSheet("color: white; background: transparent;")
        self.lbl_cond.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.c_layout.addWidget(self.lbl_city)
        self.c_layout.addWidget(self.lbl_temp)
        self.c_layout.addWidget(self.lbl_cond)
        self.c_layout.addSpacing(int(20*self.scale))
        
        # --- Grid ---
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(int(15*self.scale))
        
        self.card_feels = GlassCard("Feels Like", "🌡️")
        self.card_rain = GlassCard("Precipitation", "☔")
        self.card_uv = GlassCard("UV Index", "☀️")
        self.card_wind = GlassCard("Wind", "💨")
        self.card_hum = GlassCard("Humidity", "💧")
        self.card_vis = GlassCard("Visibility", "👁️")
        self.card_sun = GlassCard("Sunrise / Sunset", "🌅")
        
        self.grid_layout.addWidget(self.card_feels, 0, 0)
        self.grid_layout.addWidget(self.card_rain, 0, 1)
        self.grid_layout.addWidget(self.card_uv, 0, 2)
        self.grid_layout.addWidget(self.card_wind, 1, 0)
        self.grid_layout.addWidget(self.card_hum, 1, 1)
        self.grid_layout.addWidget(self.card_vis, 1, 2)
        self.grid_layout.addWidget(self.card_sun, 2, 0, 1, 3)
        
        self.c_layout.addLayout(self.grid_layout)
        self.c_layout.addSpacing(int(20*self.scale))
        
        # --- Forecast ---
        lbl_forecast = QLabel("5-Day Forecast")
        lbl_forecast.setFont(QFont("Google Sans", int(18*self.scale), QFont.Weight.Bold))
        lbl_forecast.setStyleSheet("color: rgba(255,255,255,180); background: transparent;")
        self.c_layout.addWidget(lbl_forecast)
        
        self.forecast_layout = QHBoxLayout()
        self.forecast_layout.setSpacing(int(15*self.scale))
        self.c_layout.addLayout(self.forecast_layout)
        
        self.content_scroll.setWidget(content)
        self.layout.addWidget(self.content_scroll, stretch=1)
        
        self.worker = None

    def build_nav(self):
        while self.nav_layout.count():
            item = self.nav_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for i, loc in enumerate(self.main_app.locations):
            name = loc.get("name", "Unknown")
            loc_widget = QWidget()
            loc_layout = QHBoxLayout(loc_widget)
            loc_layout.setContentsMargins(0,0,0,0)
            loc_layout.setSpacing(0)
            
            btn = QPushButton(name)
            btn.setFixedHeight(int(40*self.scale))
            if i == self.main_app.current_index:
                btn.setStyleSheet(f"background-color: rgba(255,255,255,60); color: white; border-top-left-radius: {int(20*self.scale)}px; border-bottom-left-radius: {int(20*self.scale)}px; font-weight: bold; padding: 0 {int(20*self.scale)}px; border: none;")
            else:
                btn.setStyleSheet(f"background-color: rgba(255,255,255,20); color: rgba(255,255,255,180); border-top-left-radius: {int(20*self.scale)}px; border-bottom-left-radius: {int(20*self.scale)}px; font-weight: bold; padding: 0 {int(20*self.scale)}px; border: none;")
            btn.clicked.connect(lambda checked, idx=i: self.main_app.switch_location(idx))
            
            btn_del = QPushButton("✕")
            btn_del.setFixedSize(int(30*self.scale), int(40*self.scale))
            if i == self.main_app.current_index:
                btn_del.setStyleSheet(f"background-color: rgba(255,255,255,60); color: rgba(255,255,255,150); border-top-right-radius: {int(20*self.scale)}px; border-bottom-right-radius: {int(20*self.scale)}px; font-weight: bold; padding-right: {int(10*self.scale)}px; border: none;")
            else:
                btn_del.setStyleSheet(f"background-color: rgba(255,255,255,20); color: rgba(255,255,255,100); border-top-right-radius: {int(20*self.scale)}px; border-bottom-right-radius: {int(20*self.scale)}px; font-weight: bold; padding-right: {int(10*self.scale)}px; border: none;")
            btn_del.clicked.connect(lambda checked, idx=i: self.main_app.remove_location(idx))
            
            loc_layout.addWidget(btn)
            loc_layout.addWidget(btn_del)
            self.nav_layout.addWidget(loc_widget)
            
        btn_add = QPushButton("+ Add")
        btn_add.setFixedHeight(int(40*self.scale))
        btn_add.setStyleSheet(f"background-color: rgba(0,0,0,40); color: white; border-radius: {int(20*self.scale)}px; font-weight: bold; padding: 0 {int(20*self.scale)}px; border: none;")
        btn_add.clicked.connect(self.main_app.show_add_location)
        self.nav_layout.addWidget(btn_add)
        self.nav_layout.addStretch()
        
    def fetch_data(self):
        loc = self.main_app.locations[self.main_app.current_index]
        self.lbl_city.setText(loc["name"])
        self.lbl_temp.setText("--°")
        self.lbl_cond.setText("Fetching...")
        
        if self.worker:
            self.worker.terminate()
        self.worker = FetchWeatherThread(loc["lat"], loc["lon"])
        self.worker.on_success.connect(self.update_ui)
        self.worker.on_error.connect(self.show_error)
        self.worker.start()
        
    def show_error(self, err):
        self.lbl_cond.setText(f"Error: {err}")

    def update_ui(self, data):
        c = data.get("current", {})
        d = data.get("daily", {})
        
        code = c.get("weather_code", 0)
        desc, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))
        
        self.lbl_temp.setText(f"{round(c.get('temperature_2m', 0))}°")
        self.lbl_cond.setText(desc)
        
        self.card_feels.set_value(f"{round(c.get('apparent_temperature', 0))}°")
        self.card_rain.set_value(f"{c.get('precipitation', 0)} mm")
        self.card_hum.set_value(f"{c.get('relative_humidity_2m', 0)}%")
        self.card_wind.set_value(f"{c.get('wind_speed_10m', 0)} km/h\n{c.get('wind_direction_10m', 0)}°")
        
        uvs = d.get("uv_index_max", [])
        if uvs and uvs[0] is not None:
            self.card_uv.set_value(f"{round(uvs[0], 1)}")
        else:
            self.card_uv.set_value("--")
            
        vis = c.get("visibility")
        if vis is not None:
            self.card_vis.set_value(f"{round(vis / 1000, 1)} km")
        else:
            self.card_vis.set_value("--")
            
        sunrises = d.get("sunrise", [])
        sunsets = d.get("sunset", [])
        if sunrises and sunsets:
            sr = datetime.fromisoformat(sunrises[0]).strftime("%H:%M")
            ss = datetime.fromisoformat(sunsets[0]).strftime("%H:%M")
            self.card_sun.set_value(f"☀️ {sr}    🌙 {ss}")
        else:
            self.card_sun.set_value("--")
            
        # Update Forecast
        while self.forecast_layout.count():
            item = self.forecast_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        codes = d.get("weather_code", [])
        maxs = d.get("temperature_2m_max", [])
        mins = d.get("temperature_2m_min", [])
        
        days = ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5"]
        for i in range(min(5, len(codes))):
            card = ForecastCard(days[i], codes[i], maxs[i], mins[i])
            self.forecast_layout.addWidget(card)


class WeatherPage(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.locations = []
        self.current_index = 0
        self.load_locations()
        
        self.screen_add = AddLocationScreen(self)
        self.screen_main = MainWeatherScreen(self)
        
        self.addWidget(self.screen_add)
        self.addWidget(self.screen_main)
        
        if not self.locations:
            self.setCurrentWidget(self.screen_add)
        else:
            self.switch_to_main()

    def load_locations(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.locations = data.get("locations", [])
                    self.current_index = data.get("current_index", 0)
                    if self.current_index >= len(self.locations):
                        self.current_index = 0
            except:
                pass

    def save_locations(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                "locations": self.locations,
                "current_index": self.current_index
            }, f)

    def add_location(self, loc):
        # Check if exists
        for i, existing in enumerate(self.locations):
            if existing["name"] == loc["name"]:
                self.current_index = i
                self.save_locations()
                self.switch_to_main()
                return
                
        self.locations.append(loc)
        self.current_index = len(self.locations) - 1
        self.save_locations()
        self.switch_to_main()

    def show_add_location(self):
        self.screen_add.search_input.clear()
        self.screen_add.results_list.clear()
        self.setCurrentWidget(self.screen_add)

    def switch_to_main(self):
        self.setCurrentWidget(self.screen_main)
        self.screen_main.build_nav()
        self.screen_main.fetch_data()
        
    def switch_location(self, idx):
        if 0 <= idx < len(self.locations):
            self.current_index = idx
            self.save_locations()
            self.screen_main.build_nav()
            self.screen_main.fetch_data()
            
    def remove_location(self, idx):
        if 0 <= idx < len(self.locations):
            self.locations.pop(idx)
            if self.current_index >= len(self.locations):
                self.current_index = max(0, len(self.locations) - 1)
            self.save_locations()
            
            if not self.locations:
                self.show_add_location()
            else:
                self.screen_main.build_nav()
                self.screen_main.fetch_data()