import random
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QKeyEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame
)


class SnakeBoard(QFrame):
    """The visual rendering canvas for the Snake game grid."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(520, 520)
        self.setStyleSheet("background-color: #121215; border: 2px solid #2C2C35; border-radius: 12px;")
        
        self.grid_size = 20
        self.cells_x = 520 // self.grid_size
        self.cells_y = 520 // self.grid_size
        
        self.snake = [(10, 10), (10, 11), (10, 12)]
        self.food_list = []
        self.target_food_count = 1
        
        # Customization Properties
        self.snake_color = "#4CAF50"
        self.food_color = "#E24A4A"
        self.bg_color = "#121215"

        self.direction = QPoint(0, -1)  # Moving UP initially
        self.next_direction = QPoint(0, -1)
        self.is_game_over = False
        self.is_running = False
        self.spawn_food()

    def start_new_game(self):
        self.snake = [(self.cells_x // 2, self.cells_y // 2)]
        self.direction = QPoint(0, -1)
        self.next_direction = QPoint(0, -1)
        self.is_game_over = False
        self.is_running = True
        self.food_list.clear()
        self.spawn_food()
        self.update()

    def spawn_food(self):
        """Spawns food until we reach the target food count requested by the settings panel."""
        while len(self.food_list) < self.target_food_count:
            fx = random.randint(1, self.cells_x - 2)
            fy = random.randint(1, self.cells_y - 2)
            if (fx, fy) not in self.snake and (fx, fy) not in self.food_list:
                self.food_list.append((fx, fy))

    def step(self):
        if not self.is_running or self.is_game_over:
            return False

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction.x(), head_y + self.direction.y())

        # Check wall collisions
        if (new_head[0] < 0 or new_head[0] >= self.cells_x or 
            new_head[1] < 0 or new_head[1] >= self.cells_y):
            self.is_game_over = True
            self.is_running = False
            self.update()
            return False

        # Check self collision
        if new_head in self.snake:
            self.is_game_over = True
            self.is_running = False
            self.update()
            return False

        self.snake.insert(0, new_head)

        # Check food collision across all active apples
        if new_head in self.food_list:
            self.food_list.remove(new_head)
            self.spawn_food()
            self.update()
            return True  # Scored a point!
        else:
            self.snake.pop()
            self.update()
            return False

    def set_direction(self, dx, dy):
        if (dx, dy) != (-self.direction.x(), -self.direction.y()):
            self.next_direction = QPoint(dx, dy)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Fill Background
        painter.fillRect(self.rect(), QColor(self.bg_color))

        # 2. Draw All Active Food Apples
        painter.setBrush(QColor(self.food_color))
        painter.setPen(Qt.PenStyle.NoPen)
        for fx, fy in self.food_list:
            painter.drawRoundedRect(
                fx * self.grid_size + 2, fy * self.grid_size + 2, 
                self.grid_size - 4, self.grid_size - 4, 6, 6
            )

        # 3. Draw Snake
        for idx, (sx, sy) in enumerate(self.snake):
            if idx == 0:
                painter.setBrush(QColor(self.snake_color))  # Bright head
            else:
                # Make body segments slightly darker for clean depth
                painter.setBrush(QColor(self.snake_color).darker(125))
                
            painter.drawRoundedRect(
                sx * self.grid_size + 1, sy * self.grid_size + 1, 
                self.grid_size - 2, self.grid_size - 2, 4, 4
            )

        # 4. Draw Game Over Overlay
        if self.is_game_over:
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.drawRect(self.rect())
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Arial", 32, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "GAME OVER\n\nTap Start to Retry")


class SnakePage(QWidget):
    """Standalone Classic Snake Game downloaded from GitHub App Store with Settings & Gesture Controls."""
    def __init__(self, on_close=None):
        super().__init__()
        self.score = 0
        self.high_score = 0
        self.speed_ms = 120
        self.touch_start_pos = None
        self.on_close = on_close

        # ==========================================================
        # MOVED UP: Initialize timer BEFORE building settings controls!
        # ==========================================================
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_tick)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Color Cycle Palettes
        self.snake_palettes = [("#4CAF50", "🟩 Green"), ("#3B82F6", "🟦 Blue"), ("#A855F7", "🟪 Purple"), ("#EAB308", "🨨 Yellow")]
        self.food_palettes = [("#E24A4A", "🍎 Red"), ("#F97316", "🍊 Orange"), ("#EC4899", "🌸 Pink"), ("#EAB308", "⭐ Gold")]
        self.bg_palettes = [("#121215", "🌙 Dark"), ("#000000", "⬛ Black"), ("#1E293B", "🌌 Navy"), ("#14532D", "🌲 Forest")]
        
        self.snake_idx = 0
        self.food_idx = 0
        self.bg_idx = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(30)

        # 1. Left Side: Game Grid Canvas
        self.board = SnakeBoard()
        layout.addWidget(self.board, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2. Right Side: Dashboard & Customization Menu
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # Return Home Button
        self.btn_exit = QPushButton("🏠 Return Home")
        self.btn_exit.setFixedHeight(40)
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setStyleSheet("""
            QPushButton { background-color: #2C2C35; color: white; font-size: 15px; font-weight: bold; border-radius: 8px; }
            QPushButton:hover { background-color: #E24A4A; }
        """)
        if self.on_close:
            self.btn_exit.clicked.connect(self.exit_game)
        right_panel.addWidget(self.btn_exit)

        # Title & Score Header
        header_layout = QHBoxLayout()
        title = QLabel("SNAKE")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #4CAF50;")
        
        self.lbl_score = QLabel("Score: 0")
        self.lbl_score.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.lbl_score.setStyleSheet("color: white;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_score)
        right_panel.addLayout(header_layout)

        self.lbl_high = QLabel("High Score: 0")
        self.lbl_high.setFont(QFont("Arial", 14))
        self.lbl_high.setStyleSheet("color: #888888;")
        right_panel.addWidget(self.lbl_high)

        # Start / Pause Button
        self.btn_start = QPushButton("▶ Start Game")
        self.btn_start.setFixedHeight(45)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet("background-color: #5A8DEF; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")
        self.btn_start.clicked.connect(self.toggle_game)
        right_panel.addWidget(self.btn_start)

        # =============================================================
        # INTERACTIVE SETTINGS PANEL
        # =============================================================
        settings_card = QFrame()
        settings_card.setStyleSheet("background-color: #1C1C22; border: 1px solid #2C2C35; border-radius: 12px;")
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(15, 12, 15, 12)
        settings_layout.setSpacing(10)

        lbl_settings_title = QLabel("⚙️ Game Settings")
        lbl_settings_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_settings_title.setStyleSheet("color: white; border: none;")
        settings_layout.addWidget(lbl_settings_title)

        # Option A: Speed Selector
        lbl_spd = QLabel("Speed:")
        lbl_spd.setStyleSheet("color: #AAAAAA; font-size: 13px; border: none;")
        settings_layout.addWidget(lbl_spd)

        spd_layout = QHBoxLayout()
        self.spd_buttons = []
        for label, ms in [("Slow", 160), ("Normal", 120), ("Fast", 80)]:
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, m=ms, b=btn: self.set_speed(m, b))
            spd_layout.addWidget(btn)
            self.spd_buttons.append(btn)
        settings_layout.addLayout(spd_layout)
        self.set_speed(120, self.spd_buttons[1])  # Default to Normal

        # Option B: Food Amount Selector
        lbl_fd = QLabel("Food on Screen:")
        lbl_fd.setStyleSheet("color: #AAAAAA; font-size: 13px; border: none; margin-top: 4px;")
        settings_layout.addWidget(lbl_fd)

        fd_layout = QHBoxLayout()
        self.fd_buttons = []
        for count in [1, 3, 5]:
            btn = QPushButton(f"{count} {'Apple' if count==1 else 'Apples'}")
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=count, b=btn: self.set_food_count(c, b))
            fd_layout.addWidget(btn)
            self.fd_buttons.append(btn)
        settings_layout.addLayout(fd_layout)
        self.set_food_count(1, self.fd_buttons[0])  # Default to 1 Apple

        # Option C: Custom Color Palettes
        lbl_col = QLabel("Custom Colors (Tap to Cycle):")
        lbl_col.setStyleSheet("color: #AAAAAA; font-size: 13px; border: none; margin-top: 4px;")
        settings_layout.addWidget(lbl_col)

        col_layout = QGridLayout()
        col_layout.setSpacing(8)

        self.btn_snake_col = QPushButton("Snake: 🟩 Green")
        self.btn_snake_col.setFixedHeight(34)
        self.btn_snake_col.setStyleSheet("background-color: #282830; color: white; border-radius: 6px; font-weight: bold;")
        self.btn_snake_col.clicked.connect(self.cycle_snake_color)
        col_layout.addWidget(self.btn_snake_col, 0, 0)

        self.btn_food_col = QPushButton("Food: 🍎 Red")
        self.btn_food_col.setFixedHeight(34)
        self.btn_food_col.setStyleSheet("background-color: #282830; color: white; border-radius: 6px; font-weight: bold;")
        self.btn_food_col.clicked.connect(self.cycle_food_color)
        col_layout.addWidget(self.btn_food_col, 0, 1)

        self.btn_bg_col = QPushButton("Canvas: 🌙 Dark")
        self.btn_bg_col.setFixedHeight(34)
        self.btn_bg_col.setStyleSheet("background-color: #282830; color: white; border-radius: 6px; font-weight: bold;")
        self.btn_bg_col.clicked.connect(self.cycle_bg_color)
        col_layout.addWidget(self.btn_bg_col, 1, 0, 1, 2)

        settings_layout.addLayout(col_layout)
        right_panel.addWidget(settings_card)
        layout.addLayout(right_panel)

    # =================================================================
    # SETTINGS LOGIC & CALLBACKS
    # =================================================================
    def set_speed(self, ms, active_btn):
        self.speed_ms = ms
        # SAFETY CHECK ADDED: Ensure timer exists before modifying it!
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.setInterval(self.speed_ms)
        for btn in self.spd_buttons:
            if btn == active_btn:
                btn.setStyleSheet("background-color: #5A8DEF; color: white; font-weight: bold; border-radius: 6px;")
            else:
                btn.setStyleSheet("background-color: #282830; color: #AAAAAA; border-radius: 6px;")
        self.setFocus()

    def set_food_count(self, count, active_btn):
        self.board.target_food_count = count
        self.board.spawn_food()
        self.board.update()
        for btn in self.fd_buttons:
            if btn == active_btn:
                btn.setStyleSheet("background-color: #5A8DEF; color: white; font-weight: bold; border-radius: 6px;")
            else:
                btn.setStyleSheet("background-color: #282830; color: #AAAAAA; border-radius: 6px;")
        self.setFocus()

    def cycle_snake_color(self):
        self.snake_idx = (self.snake_idx + 1) % len(self.snake_palettes)
        hex_code, label = self.snake_palettes[self.snake_idx]
        self.board.snake_color = hex_code
        self.btn_snake_col.setText(f"Snake: {label}")
        self.board.update()
        self.setFocus()

    def cycle_food_color(self):
        self.food_idx = (self.food_idx + 1) % len(self.food_palettes)
        hex_code, label = self.food_palettes[self.food_idx]
        self.board.food_color = hex_code
        self.btn_food_col.setText(f"Food: {label}")
        self.board.update()
        self.setFocus()

    def cycle_bg_color(self):
        self.bg_idx = (self.bg_idx + 1) % len(self.bg_palettes)
        hex_code, label = self.bg_palettes[self.bg_idx]
        self.board.bg_color = hex_code
        self.btn_bg_col.setText(f"Canvas: {label}")
        self.board.update()
        self.setFocus()

    # =================================================================
    # CORE GAME LOGIC & GESTURES
    # =================================================================
    def exit_game(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.board.is_running = False
        if self.on_close:
            self.on_close()

    def toggle_game(self):
        if self.board.is_game_over or not self.board.is_running:
            self.score = 0
            self.lbl_score.setText("Score: 0")
            self.board.start_new_game()
            self.timer.start(self.speed_ms)
            self.btn_start.setText("⏸ Pause")
            self.btn_start.setStyleSheet("background-color: #FF9800; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")
            self.setFocus()
        else:
            self.timer.stop()
            self.board.is_running = False
            self.btn_start.setText("▶ Resume")
            self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")

    def game_tick(self):
        scored = self.board.step()
        if scored:
            self.score += 10
            self.lbl_score.setText(f"Score: {self.score}")
            if self.score > self.high_score:
                self.high_score = self.score
                self.lbl_high.setText(f"High Score: {self.high_score}")
                
            if self.speed_ms > 50 and self.score % 50 == 0:
                self.speed_ms -= 4
                self.timer.setInterval(self.speed_ms)

        if self.board.is_game_over:
            self.timer.stop()
            self.btn_start.setText("↻ Play Again")
            self.btn_start.setStyleSheet("background-color: #E24A4A; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.touch_start_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if not self.touch_start_pos or not self.board.is_running or self.board.is_game_over:
            return

        current_pos = event.position().toPoint()
        dx = current_pos.x() - self.touch_start_pos.x()
        dy = current_pos.y() - self.touch_start_pos.y()

        if abs(dx) > 25 or abs(dy) > 25:
            if abs(dx) > abs(dy):
                if dx > 0: self.board.set_direction(1, 0)
                else:      self.board.set_direction(-1, 0)
            else:
                if dy > 0: self.board.set_direction(0, 1)
                else:      self.board.set_direction(0, -1)
            self.touch_start_pos = current_pos

    def mouseReleaseEvent(self, event):
        self.touch_start_pos = None

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key.Key_Up, Qt.Key.Key_W):     self.board.set_direction(0, -1)
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_S): self.board.set_direction(0, 1)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_A): self.board.set_direction(-1, 0)
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_D):self.board.set_direction(1, 0)
        elif key == Qt.Key.Key_Space:                self.toggle_game()
        else:                                        super().keyPressEvent(event)