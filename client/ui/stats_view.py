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
    - Title: Total Distractions
    - Total session time
    - Sleeping/Phone/Absent/GazeAway counts
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        self.title = QLabel("TOTAL DISTRACTIONS")
        self.title.setStyleSheet(
            """
            font-family: 'Courier New', monospace;
            font-size: 20px;
            font-weight: bold;
            color: #00FF41;
            background: transparent;
            """
        )
        self.title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        def make_label(text: str, font_size_px: int = 14) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"""
                font-family: 'JetBrains Mono', monospace;
                font-size: {font_size_px}px;
                color: #00FF41;
                background: transparent;
                """
            )
            lbl.setWordWrap(True)
            return lbl

        def make_value() -> QLabel:
            lbl = QLabel("0")
            lbl.setStyleSheet(
                """
                font-family: 'JetBrains Mono', monospace;
                font-size: 14px;
                font-weight: bold;
                color: #7FFF00;
                background: transparent;
                """
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return lbl

        self.lbl_session_time = make_value()
        self.lbl_sleeping = make_value()
        self.lbl_phone = make_value()
        self.lbl_absent = make_value()
        self.lbl_gaze_away = make_value()

        rows = [
            ("Total session time", self.lbl_session_time),
            ("Slept", self.lbl_sleeping),
            ("Phone", self.lbl_phone),
            ("Absent", self.lbl_absent),
            ("Looked away", self.lbl_gaze_away),
        ]

        for r, (label_text, value_lbl) in enumerate(rows):
            # Make "Total session time" slightly smaller to avoid crowding
            label_font = 13 if r == 0 else 14
            grid.addWidget(make_label(label_text, font_size_px=label_font), r, 0)
            grid.addWidget(value_lbl, r, 1)

        layout.addLayout(grid)
        layout.addStretch(1)

        self.set_summary(None)

    def set_summary(self, summary: Optional[Dict[str, Any]]):
        summary = summary or {}
        counts = summary.get("counts") or {}

        duration = summary.get("duration_seconds", 0.0)
        self.lbl_session_time.setText(_format_duration_hhmmss(duration))

        self.lbl_sleeping.setText(str(counts.get(VisionEvents.SLEEPING, 0)))
        self.lbl_phone.setText(str(counts.get(VisionEvents.PHONE_DETECTED, 0)))
        self.lbl_absent.setText(str(counts.get(VisionEvents.ABSENT, 0)))
        self.lbl_gaze_away.setText(str(counts.get(VisionEvents.GAZE_AWAY, 0)))


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

