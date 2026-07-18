import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect, QSizePolicy

# Import the background renderer and settings engine from the Kiosk OS core
from components.clockfaces import draw_custom_background, get_setting

class NeonClock(QWidget):
    # This attribute tells the App Store dynamic loader what to call this clockface
    FACE_NAME = "Neon Digital"

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.clock_layout = QVBoxLayout(self)
        self.clock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_layout.setSpacing(0)
        
        self.lbl_time = QLabel()
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_date = QLabel()
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- Create the Neon Glow Effects ---
        self.glow_time = QGraphicsDropShadowEffect()
        self.glow_time.setBlurRadius(50)  # Massive blur for a soft neon tube effect
        self.glow_time.setOffset(0, 0)    # Centered directly behind the text
        self.lbl_time.setGraphicsEffect(self.glow_time)

        self.glow_date = QGraphicsDropShadowEffect()
        self.glow_date.setBlurRadius(25)
        self.glow_date.setOffset(0, 0)
        self.lbl_date.setGraphicsEffect(self.glow_date)

        self.clock_layout.addWidget(self.lbl_time)
        self.clock_layout.addWidget(self.lbl_date)
        
        self.load_settings()

    def sizeHint(self):
        return QSize(1024, 600)

    def minimumSizeHint(self):
        return QSize(100, 100)

    def load_settings(self):
        # Automatically links to the dynamically generated editor menu
        self.color = get_setting("neon_digital_color", "#E91E63") 
        self.bg = get_setting("neon_digital_bg", "#0C0C0E")
        
        self.lbl_time.setStyleSheet(f"color: {self.color}; background: transparent;")
        self.lbl_date.setStyleSheet(f"color: {self.color}; background: transparent;")
        
        # Colorize the glowing auras to match the text perfectly
        self.glow_time.setColor(QColor(self.color))
        self.glow_date.setColor(QColor(self.color))
        
        self.resizeEvent(None)
        self.update()

    def update_time(self, t, d):
        # Including seconds so the neon clock feels active
        self.lbl_time.setText(t.toString("HH:mm:ss")) 
        self.lbl_date.setText(d.toString("dddd, MMMM d"))

    def resizeEvent(self, event):
        """Dynamically shrink the fonts when squished by the editor drawer."""
        factor = self.height() / 600.0
        
        f_time = QFont("Google Sans", max(10, int(115 * factor)), QFont.Weight.Bold)
        f_date = QFont("Google Sans", max(8, int(22 * factor)), QFont.Weight.Medium)
        
        self.lbl_time.setFont(f_time)
        self.lbl_date.setFont(f_date)
        self.clock_layout.setSpacing(max(0, int(5 * factor)))
        
        if event:
            super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Handle rounded corners correctly depending on if it's fullscreen or in the editor wrapper
        radius = 36 if self.width() < 1000 else 0
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        painter.setClipPath(path)
        
        # Use the global custom background renderer to support images, gradients, and solid colors
        draw_custom_background(painter, self.bg, self.width(), self.height())