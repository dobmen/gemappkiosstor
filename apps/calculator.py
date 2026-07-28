import operator
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QGuiApplication, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QFrame, QHBoxLayout
)

def get_scale_factor():
    screen = QGuiApplication.primaryScreen()
    return max(1.0, screen.size().width() / 1024.0) if screen else 1.0


class CalculatorPage(QWidget):
    """Sleek Touch-Friendly Calculator App"""
    def __init__(self, on_close=None):
        super().__init__()
        self.on_close = on_close
        self.scale = get_scale_factor()
        self.setStyleSheet("background-color: #0A0A0F;")
        
        self.current_input = "0"
        self.previous_input = ""
        self.operation = None
        self.new_input_started = True

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 40)
        
        # Close button at the top
        top_bar = QHBoxLayout()
        close_btn = QPushButton("✕ Close")
        close_btn.setFixedSize(int(120*self.scale), int(50*self.scale))
        close_btn.setStyleSheet(f"background-color: #1A1A24; color: white; border-radius: {int(25*self.scale)}px; font-size: {int(18*self.scale)}px;")
        close_btn.clicked.connect(self._close_app)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        main_layout.addLayout(top_bar)
        
        # Display
        self.display = QLabel(self.current_input)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.display.setStyleSheet(f"color: white; font-family: 'Google Sans'; font-size: {int(100*self.scale)}px; padding: 20px; font-weight: bold;")
        self.display.setMinimumHeight(int(180*self.scale))
        main_layout.addWidget(self.display)
        
        main_layout.addStretch()
        
        # Grid
        grid_frame = QFrame()
        grid = QGridLayout(grid_frame)
        grid.setSpacing(int(15 * self.scale))
        main_layout.addWidget(grid_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        buttons = [
            ("C", "#2C2C35", "white"), ("+/-", "#2C2C35", "white"), ("%", "#2C2C35", "white"), ("÷", "#00C3FF", "black"),
            ("7", "#1A1A24", "white"), ("8", "#1A1A24", "white"), ("9", "#1A1A24", "white"), ("×", "#00C3FF", "black"),
            ("4", "#1A1A24", "white"), ("5", "#1A1A24", "white"), ("6", "#1A1A24", "white"), ("-", "#00C3FF", "black"),
            ("1", "#1A1A24", "white"), ("2", "#1A1A24", "white"), ("3", "#1A1A24", "white"), ("+", "#00C3FF", "black"),
            ("0", "#1A1A24", "white"), (".", "#1A1A24", "white"), ("=", "#D32F2F", "white")
        ]
        
        row, col = 0, 0
        for text, bg, fg in buttons:
            btn = QPushButton(text)
            
            # Styling
            rad = int(35 * self.scale)
            font_sz = int(32 * self.scale)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {fg};
                    border-radius: {rad}px;
                    font-size: {font_sz}px;
                    font-family: 'Google Sans';
                    font-weight: bold;
                }}
                QPushButton:pressed {{
                    background-color: #555;
                }}
            """)
            
            if text == "0":
                btn.setFixedSize(int(260*self.scale), int(100*self.scale))
                grid.addWidget(btn, row, col, 1, 2)
                col += 2
            else:
                btn.setFixedSize(int(120*self.scale), int(100*self.scale))
                grid.addWidget(btn, row, col)
                col += 1
                
            if col > 3:
                col = 0
                row += 1
                
            btn.clicked.connect(lambda checked, t=text: self.on_button_click(t))

    def _close_app(self):
        if self.on_close:
            self.on_close()

    def on_button_click(self, text):
        if text.isdigit() or text == ".":
            if self.new_input_started:
                self.current_input = text if text != "." else "0."
                self.new_input_started = False
            else:
                if text == "." and "." in self.current_input: return
                self.current_input += text
        elif text == "C":
            self.current_input = "0"
            self.previous_input = ""
            self.operation = None
            self.new_input_started = True
        elif text == "+/-":
            if self.current_input != "0":
                if self.current_input.startswith("-"):
                    self.current_input = self.current_input[1:]
                else:
                    self.current_input = "-" + self.current_input
        elif text == "%":
            try:
                self.current_input = str(float(self.current_input) / 100)
                self.new_input_started = True
            except: pass
        elif text in ["+", "-", "×", "÷"]:
            if not self.new_input_started and self.operation:
                self.calculate_result()
            self.previous_input = self.current_input
            self.operation = text
            self.new_input_started = True
        elif text == "=":
            if self.operation:
                self.calculate_result()
                self.operation = None
                self.new_input_started = True
                
        # Trim .0 from integers
        if self.current_input.endswith(".0"):
            self.current_input = self.current_input[:-2]
            
        # Limit display length
        if len(self.current_input) > 12:
            self.current_input = self.current_input[:12]
            
        self.display.setText(self.current_input)

    def calculate_result(self):
        try:
            a = float(self.previous_input)
            b = float(self.current_input)
            if self.operation == "+": res = a + b
            elif self.operation == "-": res = a - b
            elif self.operation == "×": res = a * b
            elif self.operation == "÷": res = a / b if b != 0 else "Error"
            else: return
            
            if res != "Error":
                res = round(res, 8)
                self.current_input = str(res)
            else:
                self.current_input = res
        except:
            self.current_input = "Error"
