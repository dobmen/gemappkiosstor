import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QProgressBar, QFrame
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


def get_scale_factor():
    """Dynamically detects active screen resolution and returns proportional scale factor."""
    screen = QGuiApplication.primaryScreen()
    return max(1.0, screen.size().width() / 1024.0) if screen else 1.0


class BrowserPage(QWidget):
    """Touchscreen Web Browser with persistent profiles, smart navigation, and resolution scaling."""
    def __init__(self, on_close=None):
        super().__init__()
        self.scale = get_scale_factor()
        self.on_close = on_close
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. TOP NAVIGATION & ADDRESS BAR
        # -------------------------------------------------------------
        nav_bar = QFrame()
        nav_bar.setFixedHeight(int(60 * self.scale))
        nav_bar.setStyleSheet("background-color: #16161A; border-bottom: 1px solid #282830;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(int(15 * self.scale), int(8 * self.scale), int(15 * self.scale), int(8 * self.scale))
        nav_layout.setSpacing(int(10 * self.scale))

        # Return to Kiosk Home Button
        self.btn_exit = QPushButton("🏠 Home")
        self.btn_exit.setFixedSize(int(90 * self.scale), int(42 * self.scale))
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setStyleSheet(f"""
            QPushButton {{ background-color: #E24A4A; color: white; font-size: {int(15 * self.scale)}px; font-weight: bold; border-radius: 8px; }}
            QPushButton:hover {{ background-color: #C0392B; }}
        """)
        if self.on_close:
            self.btn_exit.clicked.connect(self.on_close)
        nav_layout.addWidget(self.btn_exit)

        # Back, Forward & Reload/Stop Buttons
        btn_nav_size = int(45 * self.scale)
        self.btn_back = QPushButton("◀")
        self.btn_back.setFixedSize(btn_nav_size, int(42 * self.scale))
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setEnabled(False)
        
        self.btn_forward = QPushButton("▶")
        self.btn_forward.setFixedSize(btn_nav_size, int(42 * self.scale))
        self.btn_forward.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_forward.setEnabled(False)

        self.btn_reload = QPushButton("🔄")
        self.btn_reload.setFixedSize(btn_nav_size, int(42 * self.scale))
        self.btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)

        nav_btn_style = f"""
            QPushButton {{ background-color: #282830; color: white; font-size: {int(18 * self.scale)}px; font-weight: bold; border-radius: 8px; }}
            QPushButton:hover {{ background-color: #383845; }}
            QPushButton:disabled {{ color: #555555; background-color: #1E1E24; }}
        """
        for btn in [self.btn_back, self.btn_forward, self.btn_reload]:
            btn.setStyleSheet(nav_btn_style)
            nav_layout.addWidget(btn)

        # Address / Search Input Bar
        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(int(42 * self.scale))
        self.url_bar.setPlaceholderText("Search Google or enter a website URL...")
        self.url_bar.setFont(QFont("Google Sans", int(14 * self.scale)))
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background-color: #22222A;
                color: white;
                border: 2px solid #2E2E38;
                border-radius: 8px;
                padding-left: 15px;
                padding-right: 15px;
            }
            QLineEdit:focus {
                border-color: #5A8DEF;
                background-color: #1C1C22;
            }
        """)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_layout.addWidget(self.url_bar)

        # Go / Search Button
        self.btn_go = QPushButton("🔍 Go")
        self.btn_go.setFixedSize(int(80 * self.scale), int(42 * self.scale))
        self.btn_go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_go.setStyleSheet(f"""
            QPushButton {{ background-color: #5A8DEF; color: white; font-size: {int(15 * self.scale)}px; font-weight: bold; border-radius: 8px; }}
            QPushButton:hover {{ background-color: #4A7DDF; }}
        """)
        self.btn_go.clicked.connect(self.navigate_to_url)
        nav_layout.addWidget(self.btn_go)

        layout.addWidget(nav_bar)

        # -------------------------------------------------------------
        # 2. QUICK BOOKMARKS BAR
        # -------------------------------------------------------------
        bm_bar = QFrame()
        bm_bar.setFixedHeight(int(45 * self.scale))
        bm_bar.setStyleSheet("background-color: #121215; border-bottom: 1px solid #22222A;")
        bm_layout = QHBoxLayout(bm_bar)
        bm_layout.setContentsMargins(int(15 * self.scale), int(6 * self.scale), int(15 * self.scale), int(6 * self.scale))
        bm_layout.setSpacing(int(10 * self.scale))

        lbl_bm = QLabel("⭐ Quick Links:")
        lbl_bm.setFont(QFont("Google Sans", int(13 * self.scale), QFont.Weight.Bold))
        lbl_bm.setStyleSheet("color: #AAAAAA; border: none;")
        bm_layout.addWidget(lbl_bm)

        bookmarks = [
            ("Google", "https://www.google.com"),
            ("YouTube", "https://www.youtube.com"),
            ("Wikipedia", "https://www.wikipedia.org"),
            ("GitHub", "https://www.github.com"),
            ("Reddit", "https://www.reddit.com"),
            ("DuckDuckGo", "https://duckduckgo.com")
        ]

        for title, url in bookmarks:
            btn_bm = QPushButton(title)
            btn_bm.setFixedHeight(int(30 * self.scale))
            btn_bm.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_bm.setStyleSheet(f"""
                QPushButton {{ background-color: #22222A; color: #CCCCCC; font-size: {int(13 * self.scale)}px; font-weight: bold; border-radius: 6px; padding: 0 12px; }}
                QPushButton:hover {{ background-color: #383845; color: white; }}
            """)
            btn_bm.clicked.connect(lambda checked, u=url: self.load_url_string(u))
            bm_layout.addWidget(btn_bm)

        bm_layout.addStretch()
        layout.addWidget(bm_bar)

        # -------------------------------------------------------------
        # 3. LOADING PROGRESS BAR
        # -------------------------------------------------------------
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(int(4 * self.scale))
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { background: #121215; border: none; } QProgressBar::chunk { background: #5A8DEF; }")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # -------------------------------------------------------------
        # 4. WEB ENGINE VIEW & PERSISTENT PROFILE CONFIGURATION
        # -------------------------------------------------------------
        if WEBENGINE_AVAILABLE:
            self.web = QWebEngineView()
            
            # --- PROFILE & COOKIE PERSISTENCE ---
            # Creates an isolated profile folder to permanently store cookies, cache, and logins
            self.profile = QWebEngineProfile("KioskBrowserProfile", self)
            data_path = os.path.abspath("browser_data")
            os.makedirs(data_path, exist_ok=True)
            
            self.profile.setPersistentStoragePath(data_path)
            self.profile.setCachePath(data_path)
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
            
            # --- TOUCHSCREEN & SCROLLING OPTIMIZATIONS ---
            settings = self.profile.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.TouchIconsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            
            self.page = QWebEnginePage(self.profile, self.web)
            self.web.setPage(self.page)
            self.web.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            
            # --- NAVIGATION STATE BINDINGS ---
            self.btn_back.clicked.connect(self.web.back)
            self.btn_forward.clicked.connect(self.web.forward)
            self.btn_reload.clicked.connect(self.handle_reload_stop)
            
            self.web.urlChanged.connect(self.on_url_changed)
            self.web.loadStarted.connect(self.on_load_started)
            self.web.loadProgress.connect(self.progress_bar.setValue)
            self.web.loadFinished.connect(self.on_load_finished)
            
            self.web.setUrl(QUrl("https://www.google.com"))
            layout.addWidget(self.web)
        else:
            fallback = QWidget()
            fb_layout = QVBoxLayout(fallback)
            fb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            title_lbl = QLabel("Web Engine Missing")
            title_lbl.setFont(QFont("Google Sans", int(32 * self.scale), QFont.Weight.Bold))
            title_lbl.setStyleSheet("color: white;")
            
            desc_lbl = QLabel("Please install 'PyQt6-WebEngine' in your virtual environment to render websites.")
            desc_lbl.setStyleSheet(f"color: #E24A4A; font-size: {int(18 * self.scale)}px; margin-top: 10px;")
            
            fb_layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            fb_layout.addWidget(desc_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fallback)

    def handle_reload_stop(self):
        """Toggles the reload button between Stop (if actively loading) and Reload (if finished)."""
        if WEBENGINE_AVAILABLE:
            if self.progress_bar.isVisible():
                self.web.stop()
            else:
                self.web.reload()

    def load_url_string(self, url_str):
        """Loads a URL string directly into the browser and updates the address bar."""
        self.url_bar.setText(url_str)
        if WEBENGINE_AVAILABLE:
            self.web.setUrl(QUrl(url_str))

    def navigate_to_url(self):
        """Checks if text is a URL or search query, then navigates."""
        text = self.url_bar.text().strip()
        if not text:
            return
            
        # Smart URL detection: if it contains a dot with no spaces, treat as domain
        if "." in text and " " not in text:
            if not text.startswith("http://") and not text.startswith("https://"):
                text = "https://" + text
        else:
            # Treat plain words or phrases as a Google search query
            query = text.replace(" ", "+")
            text = f"https://www.google.com/search?q={query}"
            
        self.load_url_string(text)

    def on_load_started(self):
        """Shows progress bar and changes reload button into a Stop ('✕') icon."""
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.btn_reload.setText("✕")

    def on_load_finished(self):
        """Hides progress bar, restores Reload icon, and updates Back/Forward enabled states."""
        self.progress_bar.hide()
        self.btn_reload.setText("🔄")
        if WEBENGINE_AVAILABLE:
            self.btn_back.setEnabled(self.web.history().canGoBack())
            self.btn_forward.setEnabled(self.web.history().canGoForward())

    def on_url_changed(self, qurl):
        """Updates the address bar when navigating between webpages via links."""
        self.url_bar.setText(qurl.toString())
        if WEBENGINE_AVAILABLE:
            self.btn_back.setEnabled(self.web.history().canGoBack())
            self.btn_forward.setEnabled(self.web.history().canGoForward())