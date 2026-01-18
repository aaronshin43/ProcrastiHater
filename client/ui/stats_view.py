import os
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)

from shared.constants import VisionEvents
import client.ui.name as name


def _format_duration_hhmmss(seconds: float) -> str:
    try:
        total = max(0, int(seconds))
    except Exception:
        total = 0
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _personality_to_image_filename(personality: str) -> str:
    # Prefer the same mapping used by FloatingWidget.
    try:
        from client.ui.floating_widget import FloatingWidget

        if personality in FloatingWidget.PERSONALITY_IMAGE_MAP:
            return FloatingWidget.PERSONALITY_IMAGE_MAP[personality]
    except Exception:
        pass

    # Fallback: scan personality_cards
    for icon, title, _desc in getattr(name, "personality_cards", []):
        if title == personality:
            return icon

    return "test.png"


class _GreenBorderPanel(QWidget):
    """Black panel with 10px inset green border (Pip-Boy style)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(10, 10, -10, -10)
        pen = QPen(QColor(0, 255, 65), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        super().paintEvent(event)


class StatsSummaryWidget(_GreenBorderPanel):
    """
    Left box:
    - Big Total Violations Count
    - Session Time
    - Detailed Breakdown
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)

        # --- Header Section ---
        header = QLabel("SESSION REPORT")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-family: 'Courier New'; font-size: 22px; font-weight: bold; color: #00FF41; letter-spacing: 2px;")
        layout.addWidget(header)

        layout.addSpacing(10)

        # --- Total Violations (The Impactful Part) ---
        self.lbl_total_violations = QLabel("0")
        self.lbl_total_violations.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_total_violations.setStyleSheet(
            """
            font-family: 'Courier New'; 
            font-size: 96px; 
            font-weight: bold; 
            color: #00FF41;
            """
        )
        layout.addWidget(self.lbl_total_violations)

        self.lbl_total_sub = QLabel("TOTAL VIOLATIONS")
        self.lbl_total_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_total_sub.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 14px; color: #00AA22;")
        layout.addWidget(self.lbl_total_sub)

        layout.addSpacing(30)

        # --- Session Duration ---
        self.lbl_duration_val = QLabel("00:00:00")
        self.lbl_duration_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_duration_val.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 28px; font-weight: bold; color: #00FF41;")
        layout.addWidget(self.lbl_duration_val)

        lbl_duration_sub = QLabel("SESSION DURATION")
        lbl_duration_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_duration_sub.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 12px; color: #00AA22;")
        layout.addWidget(lbl_duration_sub)

        layout.addSpacing(30)

        # --- Divider ---
        divider = QLabel()
        divider.setFixedHeight(2)
        divider.setStyleSheet("background-color: #005511;")
        layout.addWidget(divider)
        
        layout.addSpacing(20)

        # --- Details List (Grid) ---
        details_container = QWidget()
        details_layout = QGridLayout(details_container)
        details_layout.setContentsMargins(20, 0, 20, 0)
        details_layout.setVerticalSpacing(15)
        details_layout.setHorizontalSpacing(20)

        self.detail_map = {
            "PHONE ADDICTION": (VisionEvents.PHONE_DETECTED, QLabel("0")),
            "SLEEPING": (VisionEvents.SLEEPING, QLabel("0")),
            "ABSENT": (VisionEvents.ABSENT, QLabel("0")),
            "UNKNOWN GLAZE": (VisionEvents.GAZE_AWAY, QLabel("0")),
            "SCREEN PLAY": ("DISTRACTING_ACTIVITY", QLabel("0")),
        }

        row = 0
        for label, (event_key, value_widget) in self.detail_map.items():
            # Label
            lbl_name = QLabel(label)
            lbl_name.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 14px; color: #00FF41;")
            
            # Value
            value_widget.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 16px; font-weight: bold; color: #00FF41;")
            value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)

            details_layout.addWidget(lbl_name, row, 0)
            details_layout.addWidget(value_widget, row, 1)
            row += 1

        layout.addWidget(details_container)
        layout.addStretch(1)

        self.set_summary(None)

    def set_summary(self, summary: Optional[Dict[str, Any]]):
        summary = summary or {}
        counts = summary.get("counts") or {}
        total_violations = int(summary.get("total_violations", 0))
        duration = summary.get("duration_seconds", 0.0)

        # Update Top Stats
        self.lbl_total_violations.setText(str(total_violations))
        self.lbl_duration_val.setText(_format_duration_hhmmss(duration))
        
        # Critical Style for High Violations
        if total_violations > 0:
            # Red warning color for violations
            self.lbl_total_violations.setStyleSheet(
                """
                font-family: 'Courier New'; 
                font-size: 96px; 
                font-weight: bold; 
                color: #FF3333;
                text-shadow: 0 0 10px #FF0000;
                """
            )
            self.lbl_total_sub.setText("VIOLATIONS DETECTED")
            self.lbl_total_sub.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 14px; color: #CC2222;")
        else:
            self.lbl_total_violations.setStyleSheet(
                """
                font-family: 'Courier New'; 
                font-size: 96px; 
                font-weight: bold; 
                color: #00FF41;
                """
            )
            self.lbl_total_sub.setText("PERFECT SESSION")
            self.lbl_total_sub.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 14px; color: #00AA22;")

        # Update Details
        for label, (event_key, widget) in self.detail_map.items():
            count = counts.get(event_key, 0)
            widget.setText(f"{count}")


class StatsFeedbackWidget(_GreenBorderPanel):
    """
    Right box:
    - personality image
    - feedback text (English, from Gemini)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.image_label = QLabel("")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label, 2)

        self.feedback_label = QLabel("Generating feedback...")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.feedback_label.setStyleSheet(
            """
            font-family: 'JetBrains Mono', monospace;
            font-size: 16px;
            color: #00FF41;
            background: transparent;
            """
        )
        layout.addWidget(self.feedback_label, 1)

        self.set_personality(getattr(name, "user_personality", "") or "")

    def set_personality(self, personality: str):
        filename = _personality_to_image_filename(personality)
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        image_path = os.path.join(assets_dir, filename)
        if not os.path.exists(image_path):
            image_path = os.path.join(assets_dir, "test.png")

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("")
            return

        scaled = pixmap.scaled(
            500,
            500,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def set_feedback_text(self, text: str):
        self.feedback_label.setText(text or "")

