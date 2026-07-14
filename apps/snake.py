import random
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QKeyEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
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
        self.food = (15, 15)
        self.direction = QPoint(0, -1)  # Moving UP initially
        self.next_direction = QPoint(0, -1)
        self.is_game_over = False
        self.is_running = False

    def start_new_game(self):
        self.snake = [(self.cells_x // 2, self.cells_y // 2)]
        self.direction = QPoint(0, -1)
        self.next_direction = QPoint(0, -1)
        self.is_game_over = False
        self.is_running = True
        self.spawn_food()
        self.update()

    def spawn_food(self):
        while True:
            fx = random.randint(1, self.cells_x - 2)
            fy = random.randint(1, self.cells_y - 2)
            if (fx, fy) not in self.snake:
                self.food = (fx, fy)
                break

    def step(self):
        if not self.is_running or self.is_game_over:
            return False

        # Apply buffered direction
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

        # Check food collision
        if new_head == self.food:
            self.spawn_food()
            self.update()
            return True  # Scored a point!
        else:
            self.snake.pop()
            self.update()
            return False

    def set_direction(self, dx, dy):
        # Prevent 180-degree instant reverse suicides
        if (dx, dy) != (-self.direction.x(), -self.direction.y()):
            self.next_direction = QPoint(dx, dy)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw Food (Red Apple)
        painter.setBrush(QColor("#E24A4A"))
        painter.setPen(Qt.PenStyle.NoPen)
        fx, fy = self.food
        painter.drawRoundedRect(
            fx * self.grid_size + 2, fy * self.grid_size + 2, 
            self.grid_size - 4, self.grid_size - 4, 6, 6
        )

        # Draw Snake
        for idx, (sx, sy) in enumerate(self.snake):
            if idx == 0:
                painter.setBrush(QColor("#4CAF50"))  # Bright green head
            else:
                painter.setBrush(QColor("#2E7D32"))  # Darker green body
                
            painter.drawRoundedRect(
                sx * self.grid_size + 1, sy * self.grid_size + 1, 
                self.grid_size - 2, self.grid_size - 2, 4, 4
            )

        # Draw Game Over Overlay
        if self.is_game_over:
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.drawRect(self.rect())
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Arial", 32, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "GAME OVER\n\nTap Start to Retry")


class SnakePage(QWidget):
    """Standalone Classic Snake Game downloaded from GitHub App Store with Gesture Controls."""
    def __init__(self):
        super().__init__()
        self.score = 0
        self.high_score = 0
        self.speed_ms = 120  # Game tick speed
        self.touch_start_pos = None  # Tracks swipe gesture origin

        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(40)

        # 1. Left Side: Game Grid Canvas
        self.board = SnakeBoard()
        layout.addWidget(self.board, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2. Right Side: Dashboard & Gesture Guide
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        # Title & Score
        title = QLabel("SNAKE")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setStyleSheet("color: #4CAF50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(title)

        self.lbl_score = QLabel("Score: 0")
        self.lbl_score.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.lbl_score.setStyleSheet("color: white;")
        self.lbl_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(self.lbl_score)

        self.lbl_high = QLabel("High Score: 0")
        self.lbl_high.setFont(QFont("Arial", 16))
        self.lbl_high.setStyleSheet("color: #888888;")
        self.lbl_high.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(self.lbl_high)

        # Start / Pause Button
        self.btn_start = QPushButton("▶ Start Game")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet("background-color: #5A8DEF; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")
        self.btn_start.clicked.connect(self.toggle_game)
        right_panel.addWidget(self.btn_start)

        right_panel.addStretch()

        # Visual Gesture Instructions Card (Replaced the D-Pad!)
        hint_card = QFrame()
        hint_card.setStyleSheet("background-color: #1C1C22; border: 1px solid #2C2C35; border-radius: 14px;")
        hint_layout = QVBoxLayout(hint_card)
        hint_layout.setContentsMargins(20, 20, 20, 20)
        hint_layout.setSpacing(12)
        hint_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_icon = QLabel("👆")
        lbl_icon.setFont(QFont("Arial", 36))
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("border: none;")

        lbl_hint_title = QLabel("Swipe Controls")
        lbl_hint_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_hint_title.setStyleSheet("color: white; border: none;")
        lbl_hint_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_hint_desc = QLabel("Swipe anywhere on the screen UP, DOWN, LEFT, or RIGHT to steer your snake!\n\n(Keyboard Arrow Keys & WASD also supported)")
        lbl_hint_desc.setFont(QFont("Arial", 13))
        lbl_hint_desc.setStyleSheet("color: #AAAAAA; border: none;")
        lbl_hint_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_hint_desc.setWordWrap(True)

        hint_layout.addWidget(lbl_icon)
        hint_layout.addWidget(lbl_hint_title)
        hint_layout.addWidget(lbl_hint_desc)
        right_panel.addWidget(hint_card)

        right_panel.addStretch()
        layout.addLayout(right_panel)

        # Game Loop Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_tick)

        # Enable keyboard focus for arrow keys
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def toggle_game(self):
        if self.board.is_game_over or not self.board.is_running:
            self.score = 0
            self.lbl_score.setText("Score: 0")
            self.board.start_new_game()
            self.timer.start(self.speed_ms)
            self.btn_start.setText("⏸ Pause")
            self.btn_start.setStyleSheet("background-color: #FF9800; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")
            self.setFocus()  # Grab keyboard focus
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
                
            # Slightly speed up as you get longer!
            if self.speed_ms > 60 and self.score % 50 == 0:
                self.speed_ms -= 5
                self.timer.setInterval(self.speed_ms)

        if self.board.is_game_over:
            self.timer.stop()
            self.btn_start.setText("↻ Play Again")
            self.btn_start.setStyleSheet("background-color: #E24A4A; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")

    # =================================================================
    # TOUCHSCREEN SWIPE ENGINE
    # =================================================================
    def mousePressEvent(self, event):
        """Records the starting position of a touchscreen swipe."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.touch_start_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        """Detects real-time finger dragging and triggers turns instantly!"""
        if not self.touch_start_pos or not self.board.is_running or self.board.is_game_over:
            return

        current_pos = event.position().toPoint()
        dx = current_pos.x() - self.touch_start_pos.x()
        dy = current_pos.y() - self.touch_start_pos.y()

        # Trigger turn immediately once finger moves more than 25 pixels
        if abs(dx) > 25 or abs(dy) > 25:
            if abs(dx) > abs(dy):
                if dx > 0:
                    self.board.set_direction(1, 0)   # Swipe Right ▶
                else:
                    self.board.set_direction(-1, 0)  # Swipe Left ◀
            else:
                if dy > 0:
                    self.board.set_direction(0, 1)   # Swipe Down ▼
                else:
                    self.board.set_direction(0, -1)  # Swipe Up ▲

            # Reset origin to current position so you can zigzag without lifting your finger!
            self.touch_start_pos = current_pos

    def mouseReleaseEvent(self, event):
        """Clears tracking when finger lifts off the screen."""
        self.touch_start_pos = None

    # =================================================================
    # KEYBOARD CONTROLS (WASD & Arrows)
    # =================================================================
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key.Key_Up, Qt.Key.Key_W):
            self.board.set_direction(0, -1)
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_S):
            self.board.set_direction(0, 1)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self.board.set_direction(-1, 0)
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self.board.set_direction(1, 0)
        elif key == Qt.Key.Key_Space:
            self.toggle_game()
        else:
            super().keyPressEvent(event)