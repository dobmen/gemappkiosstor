import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
    WEBENGINE_AVAILABLE = True
except Exception as e:
    WEBENGINE_AVAILABLE = False
    WEBENGINE_ERROR = str(e)


def get_scale_factor():
    screen = QGuiApplication.primaryScreen()
    return max(1.0, screen.size().width() / 1024.0) if screen else 1.0


class YoutubePage(QWidget):
    """YouTube TV App with persistent login and Smart TV layout spoofing."""
    def __init__(self, on_close=None):
        super().__init__()
        self.scale = get_scale_factor()
        self.on_close = on_close
        self.setStyleSheet("background-color: #0C0C0E;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. TOP NAV BAR (EXIT BUTTON)
        # -------------------------------------------------------------
        # We need a way to exit the app since it's full screen without OS chrome
        top_bar = QFrame()
        top_bar.setFixedHeight(int(54 * self.scale))
        top_bar.setStyleSheet("background-color: #121215; border-bottom: 1px solid #282830;")
        
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(int(15 * self.scale), int(7 * self.scale), int(15 * self.scale), int(7 * self.scale))
        top_layout.setSpacing(int(15 * self.scale))
        
        self.btn_exit = QPushButton("🏠 Home")
        self.btn_exit.setFixedSize(int(100 * self.scale), int(40 * self.scale))
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setStyleSheet(f"""
            QPushButton {{ background-color: #E24A4A; color: white; font-size: {int(15 * self.scale)}px; font-weight: bold; border-radius: 8px; }}
            QPushButton:hover {{ background-color: #C0392B; }}
        """)
        if self.on_close:
            self.btn_exit.clicked.connect(self.on_close)
            
        top_layout.addWidget(self.btn_exit)
        
        # Add a title label just to fill space nicely
        title_lbl = QLabel("YouTube")
        title_lbl.setFont(QFont("Google Sans", int(18 * self.scale), QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white;")
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()
        
        layout.addWidget(top_bar)

        # -------------------------------------------------------------
        # 2. WEB ENGINE VIEW & PERSISTENT PROFILE
        # -------------------------------------------------------------
        if WEBENGINE_AVAILABLE:
            self.web = QWebEngineView()
            
            # Use a totally isolated profile to store YouTube cookies permanently
            self.profile = QWebEngineProfile("YouTubeTVProfile", self)
            data_path = os.path.abspath("youtube_data")
            os.makedirs(data_path, exist_ok=True)
            
            self.profile.setPersistentStoragePath(data_path)
            self.profile.setCachePath(data_path)
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
            
            # --- SPOOF USER AGENT TO FORCE SMART TV INTERFACE ---
            self.profile.setHttpUserAgent("Mozilla/5.0 (SMART-TV; Linux; Tizen 5.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/5.0 TV Safari/538.1")
            
            # Optimizations
            settings = self.profile.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            
            self.page = QWebEnginePage(self.profile, self.web)
            self.web.setPage(self.page)
            self.web.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            
            self.web.setUrl(QUrl("https://www.youtube.com/tv"))
            layout.addWidget(self.web)
        else:
            fallback = QWidget()
            fb_layout = QVBoxLayout(fallback)
            fb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            title_lbl = QLabel("YouTube Missing Engine")
            title_lbl.setFont(QFont("Google Sans", int(32 * self.scale), QFont.Weight.Bold))
            title_lbl.setStyleSheet("color: white;")
            
            desc_lbl = QLabel(f"WebEngine failed to load:\\n{WEBENGINE_ERROR}\\n\\nPlease install 'PyQt6-WebEngine'.")
            desc_lbl.setStyleSheet(f"color: #E24A4A; font-size: {int(18 * self.scale)}px; margin-top: 10px;")
            
            fb_layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            fb_layout.addWidget(desc_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fallback)
