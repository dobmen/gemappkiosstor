import os
import json
import urllib.request
import urllib.parse
from datetime import datetime
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QGuiApplication, QColor, QPainter, QLinearGradient, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QFrame, QScrollArea, QLineEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QSizePolicy, QScroller
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
            f"daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max&"
            f"hourly=temperature_2m,precipitation,wind_speed_10m,uv_index&forecast_days=10&timezone=auto"
        )
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.on_success.emit(data)
        except Exception as e:
            self.on_error.emit(str(e))


class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.scale = get_scale_factor()
        self.data = []
        self.labels = []
        self.mode = "line"
        self.color = QColor("#5A8DEF")
        self.selected_index = -1
        
    def set_data(self, data, labels, mode="line", color="#5A8DEF"):
        self.data = data
        self.labels = labels
        self.mode = mode
        self.color = QColor(color)
        self.selected_index = -1
        self.update()
        
    def mousePressEvent(self, event):
        if not self.data: return
        w = self.width()
        pad_l = int(60 * self.scale)
        pad_r = int(20 * self.scale)
        graph_w = w - pad_l - pad_r
        
        x = event.pos().x()
        if x < pad_l or x > pad_l + graph_w:
            self.selected_index = -1
        else:
            n = len(self.data)
            step_x = graph_w / (n - 1) if self.mode == "line" else graph_w / n
            # For bar, there is an offset
            if self.mode == "bar":
                idx = int((x - pad_l) / step_x)
            else:
                idx = round((x - pad_l) / step_x)
            self.selected_index = max(0, min(n - 1, idx))
        self.update()
        
    def paintEvent(self, event):
        if not self.data: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        pad_l = int(60 * self.scale)
        pad_r = int(20 * self.scale)
        pad_t = int(30 * self.scale)
        pad_b = int(40 * self.scale)
        
        graph_w = w - pad_l - pad_r
        graph_h = h - pad_t - pad_b
        
        min_v = min(self.data)
        max_v = max(self.data)
        
        if self.mode == "bar":
            min_v = 0
            if max_v == 0: max_v = 1
        else:
            if max_v == min_v:
                max_v += 1
                min_v -= 1
                
        rng = max_v - min_v
        
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
        painter.drawLine(pad_l, pad_t, pad_l + graph_w, pad_t)
        painter.drawLine(pad_l, pad_t + graph_h, pad_l + graph_w, pad_t + graph_h)
        
        painter.setPen(QPen(QColor(255, 255, 255, 150)))
        painter.setFont(QFont("Google Sans", int(12 * self.scale)))
        painter.drawText(0, pad_t - 10, pad_l - 10, 20, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{max_v:.1f}")
        painter.drawText(0, pad_t + graph_h - 10, pad_l - 10, 20, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{min_v:.1f}")
        
        n = len(self.data)
        if n < 2: return
        
        step_x = graph_w / (n - 1) if self.mode == "line" else graph_w / n
        
        if self.mode == "line":
            path = QPainterPath()
            for i, val in enumerate(self.data):
                x = pad_l + i * step_x
                y = pad_t + graph_h - ((val - min_v) / rng * graph_h)
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            
            pen = QPen(self.color, 3)
            painter.setPen(pen)
            painter.drawPath(path)
            
            path.lineTo(pad_l + graph_w, pad_t + graph_h)
            path.lineTo(pad_l, pad_t + graph_h)
            
            grad = QLinearGradient(0, pad_t, 0, pad_t + graph_h)
            fill_color = QColor(self.color)
            fill_color.setAlpha(100)
            grad.setColorAt(0, fill_color)
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillPath(path, grad)
            
        elif self.mode == "bar":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.color)
            bar_w = max(2, int(step_x * 0.7))
            for i, val in enumerate(self.data):
                if val <= 0: continue
                x = pad_l + i * step_x + (step_x - bar_w) / 2
                bh = (val / max_v) * graph_h
                y = pad_t + graph_h - bh
                painter.drawRect(int(x), int(y), int(bar_w), int(bh))
                
        painter.setPen(QPen(QColor(255, 255, 255, 150)))
        for i, lbl in enumerate(self.labels):
            if i % max(1, (n // 6)) == 0:
                x = pad_l + i * step_x + (step_x / 2 if self.mode == "bar" else 0)
                painter.drawText(int(x) - 30, pad_t + graph_h + 10, 60, 20, Qt.AlignmentFlag.AlignCenter, lbl)
                
        if hasattr(self, 'selected_index') and self.selected_index != -1 and self.selected_index < len(self.data):
            idx = self.selected_index
            val = self.data[idx]
            lbl = self.labels[idx]
            
            x = pad_l + idx * step_x + (step_x / 2 if self.mode == "bar" else 0)
            
            painter.setPen(QPen(QColor(255, 255, 255, 200), 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(x), pad_t, int(x), pad_t + graph_h)
            
            if self.mode == "line":
                y = pad_t + graph_h - ((val - min_v) / rng * graph_h)
            else:
                y = pad_t + graph_h - (val / max_v * graph_h)
                
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)
            
            text = f"{lbl}  |  {val:.1f}"
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text) + 20
            th = fm.height() + 10
            tx = int(x) - tw // 2
            if tx < pad_l: tx = pad_l
            if tx + tw > w - pad_r: tx = w - pad_r - tw
            ty = int(y) - th - 10
            if ty < 0: ty = int(y) + 10
            
            painter.setBrush(QColor(0, 0, 0, 220))
            painter.drawRoundedRect(tx, ty, tw, th, 5, 5)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(tx, ty, tw, th, Qt.AlignmentFlag.AlignCenter, text)


class DetailPopup(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.scale = get_scale_factor()
        self.hide()
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.container = QFrame()
        self.container.setFixedSize(int(700*self.scale), int(450*self.scale))
        self.container.setStyleSheet("background-color: #1A1A22; border-radius: 20px; border: 1px solid #333340;")
        
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(int(30*self.scale), int(30*self.scale), int(30*self.scale), int(30*self.scale))
        
        header = QHBoxLayout()
        self.lbl_title = QLabel("Details")
        self.lbl_title.setFont(QFont("Google Sans", int(24*self.scale), QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: white; background: transparent; border: none;")
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(int(40*self.scale), int(40*self.scale))
        btn_close.setStyleSheet("QPushButton { background-color: rgba(255,255,255,20); color: white; border-radius: 20px; border: none; } QPushButton:hover { background-color: #E24A4A; }")
        btn_close.clicked.connect(self.hide)
        
        header.addWidget(self.lbl_title)
        header.addStretch()
        header.addWidget(btn_close)
        c_layout.addLayout(header)
        
        self.graph = GraphWidget()
        c_layout.addWidget(self.graph, stretch=1)
        
        self.toggles_layout = QHBoxLayout()
        self.toggles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toggles_layout.setSpacing(int(15*self.scale))
        c_layout.addLayout(self.toggles_layout)
        
        layout.addWidget(self.container)
        
        self.current_data = {}
        self.current_labels = []

    def set_title(self, title):
        self.lbl_title.setText(title)
        
    def populate(self, data_dict, labels):
        self.current_data = data_dict
        self.current_labels = labels
        
        while self.toggles_layout.count():
            item = self.toggles_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for key in data_dict.keys():
            btn = QPushButton(key.capitalize())
            btn.setFixedHeight(int(36*self.scale))
            btn.setStyleSheet(f"background-color: rgba(255,255,255,20); color: white; border-radius: {int(18*self.scale)}px; font-weight: bold; padding: 0 {int(15*self.scale)}px; border: none;")
            btn.clicked.connect(lambda checked, k=key: self.show_metric(k))
            self.toggles_layout.addWidget(btn)
            
        if data_dict:
            self.show_metric(list(data_dict.keys())[0])
            self.raise_()
            self.show()
            
    def show_metric(self, key):
        if key in self.current_data:
            color = "#5A8DEF"
            mode = "line"
            if key.lower() == "precipitation":
                mode = "bar"
                color = "#3EA6FF"
            elif key.lower() == "uv index":
                color = "#F39C12"
            elif key.lower() == "wind":
                color = "#8E44AD"
            self.graph.set_data(self.current_data[key], self.current_labels, mode, color)

    def mousePressEvent(self, event):
        if not self.container.geometry().contains(event.pos()):
            self.hide()


class GlassCard(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self, title, icon, metric_id, value="--"):
        super().__init__()
        self.metric_id = metric_id
        self.scale = get_scale_factor()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            GlassCard {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
            GlassCard:hover {
                background-color: rgba(255, 255, 255, 50);
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
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.metric_id)
        super().mouseReleaseEvent(event)


class ForecastCard(QFrame):
    clicked = pyqtSignal(int)
    def __init__(self, index, day_name, code, max_temp, min_temp):
        super().__init__()
        self.index = index
        self.scale = get_scale_factor()
        self.setFixedSize(int(130 * self.scale), int(140 * self.scale))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            ForecastCard {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 16px;
            }
            ForecastCard:hover {
                background-color: rgba(255, 255, 255, 50);
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

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
        super().mouseReleaseEvent(event)


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
        self.last_data = {}
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(int(20*self.scale), int(20*self.scale), int(20*self.scale), int(20*self.scale))
        
        # --- Top Nav ---
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setFixedHeight(int(70*self.scale))
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        QScroller.grabGesture(self.nav_scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        
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
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        QScroller.grabGesture(self.content_scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        
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
        
        # --- Forecast ---
        lbl_forecast = QLabel("10-Day Forecast")
        lbl_forecast.setFont(QFont("Google Sans", int(18*self.scale), QFont.Weight.Bold))
        lbl_forecast.setStyleSheet("color: rgba(255,255,255,180); background: transparent;")
        self.c_layout.addWidget(lbl_forecast)
        
        self.forecast_scroll = QScrollArea()
        self.forecast_scroll.setFixedHeight(int(170*self.scale))
        self.forecast_scroll.setWidgetResizable(True)
        self.forecast_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.forecast_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.forecast_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        QScroller.grabGesture(self.forecast_scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        
        self.forecast_container = QWidget()
        self.forecast_container.setStyleSheet("background: transparent;")
        self.forecast_layout = QHBoxLayout(self.forecast_container)
        self.forecast_layout.setContentsMargins(0,0,0,0)
        self.forecast_layout.setSpacing(int(15*self.scale))
        self.forecast_scroll.setWidget(self.forecast_container)
        
        self.c_layout.addWidget(self.forecast_scroll)
        self.c_layout.addSpacing(int(20*self.scale))
        
        # --- Grid ---
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(int(15*self.scale))
        
        self.card_feels = GlassCard("Feels Like", "🌡️", "temperature_2m")
        self.card_rain = GlassCard("Precipitation", "☔", "precipitation")
        self.card_uv = GlassCard("UV Index", "☀️", "uv_index")
        self.card_wind = GlassCard("Wind", "💨", "wind_speed_10m")
        self.card_hum = GlassCard("Humidity", "💧", "humidity")
        self.card_vis = GlassCard("Visibility", "👁️", "visibility")
        self.card_sun = GlassCard("Sunrise / Sunset", "🌅", "sunrise")
        
        self.card_feels.clicked.connect(self.on_metric_clicked)
        self.card_rain.clicked.connect(self.on_metric_clicked)
        self.card_uv.clicked.connect(self.on_metric_clicked)
        self.card_wind.clicked.connect(self.on_metric_clicked)
        
        self.grid_layout.addWidget(self.card_feels, 0, 0)
        self.grid_layout.addWidget(self.card_rain, 0, 1)
        self.grid_layout.addWidget(self.card_uv, 0, 2)
        self.grid_layout.addWidget(self.card_wind, 1, 0)
        self.grid_layout.addWidget(self.card_hum, 1, 1)
        self.grid_layout.addWidget(self.card_vis, 1, 2)
        self.grid_layout.addWidget(self.card_sun, 2, 0, 1, 3)
        
        self.c_layout.addLayout(self.grid_layout)
        
        self.content_scroll.setWidget(content)
        self.layout.addWidget(self.content_scroll, stretch=1)
        
        self.worker = None
        self.popup = DetailPopup(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.popup.setGeometry(self.rect())

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
        self.last_data = data
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
        times = d.get("time", [])
        
        for i in range(min(10, len(codes))):
            day_name = "Today" if i == 0 else "Tomorrow" if i == 1 else datetime.fromisoformat(times[i]).strftime("%A")
            card = ForecastCard(i, day_name, codes[i], maxs[i], mins[i])
            card.clicked.connect(self.on_day_clicked)
            self.forecast_layout.addWidget(card)

    def on_metric_clicked(self, metric_id):
        if not self.last_data or metric_id not in ["temperature_2m", "precipitation", "wind_speed_10m", "uv_index"]:
            return
        self.open_graph_for_day(0, default_metric=metric_id)

    def on_day_clicked(self, day_index):
        if not self.last_data: return
        self.open_graph_for_day(day_index)
        
    def open_graph_for_day(self, day_index, default_metric="temperature_2m"):
        h = self.last_data.get("hourly", {})
        d = self.last_data.get("daily", {})
        
        start_idx = day_index * 24
        end_idx = start_idx + 24
        
        labels = [f"{i}:00" for i in range(24)]
        
        data_dict = {}
        if "temperature_2m" in h:
            data_dict["Temperature"] = h["temperature_2m"][start_idx:end_idx]
        if "precipitation" in h:
            data_dict["Precipitation"] = h["precipitation"][start_idx:end_idx]
        if "wind_speed_10m" in h:
            data_dict["Wind"] = h["wind_speed_10m"][start_idx:end_idx]
        if "uv_index" in h:
            data_dict["UV Index"] = h["uv_index"][start_idx:end_idx]
            
        times = d.get("time", [])
        day_str = "Selected Day"
        if day_index < len(times):
            day_str = datetime.fromisoformat(times[day_index]).strftime("%A, %b %d")
            
        self.popup.set_title(day_str)
        
        # map metric_id to pretty name
        mapping = {
            "temperature_2m": "Temperature",
            "precipitation": "Precipitation",
            "wind_speed_10m": "Wind",
            "uv_index": "UV Index"
        }
        
        self.popup.populate(data_dict, labels)
        if mapping.get(default_metric) in data_dict:
            self.popup.show_metric(mapping[default_metric])


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