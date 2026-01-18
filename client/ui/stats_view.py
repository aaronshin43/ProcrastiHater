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


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _compute_focus_score(slept: int, phone: int, absent: int, looked_away: int) -> int:
    penalty = slept * 15 + phone * 20 + absent * 10 + looked_away * 5
    return max(0, 100 - penalty)


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

        # KPI: big number
        kpi_row = QHBoxLayout()
        kpi_row.setContentsMargins(0, 0, 0, 0)
        kpi_row.setSpacing(10)

        self.kpi_label = QLabel("DISTRACTIONS")
        self.kpi_label.setStyleSheet(
            """
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: #00FF41;
            background: transparent;
            """
        )
        self.kpi_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        self.kpi_value = QLabel("0")
        self.kpi_value.setStyleSheet(
            """
            font-family: 'Courier New', monospace;
            font-size: 56px;
            font-weight: bold;
            color: #7FFF00;
            background: transparent;
            """
        )
        self.kpi_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        kpi_row.addWidget(self.kpi_label, 0)
        kpi_row.addStretch(1)
        kpi_row.addWidget(self.kpi_value, 0)
        layout.addLayout(kpi_row)

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

        # Meta
        self.lbl_session_time = make_value()
        self.lbl_focus_score = make_value()

        # Progress bars
        from PyQt6.QtWidgets import QProgressBar

        def make_bar() -> QProgressBar:
            bar = QProgressBar()
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setRange(0, 1)
            bar.setValue(0)
            bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #00FF41;
                    background-color: #000000;
                }
                QProgressBar::chunk {
                    background-color: #00FF41;
                }
                """
            )
            return bar

        self.lbl_sleeping = make_value()
        self.lbl_phone = make_value()
        self.lbl_absent = make_value()
        self.lbl_gaze_away = make_value()

        self.bar_sleeping = make_bar()
        self.bar_phone = make_bar()
        self.bar_absent = make_bar()
        self.bar_gaze_away = make_bar()

        # Row 0-1: meta
        grid.addWidget(make_label("Total session time", font_size_px=13), 0, 0)
        grid.addWidget(self.lbl_session_time, 0, 2)

        grid.addWidget(make_label("Focus score", font_size_px=13), 1, 0)
        grid.addWidget(self.lbl_focus_score, 1, 2)

        # Rows 2-5: bars
        metric_rows = [
            ("Slept", self.bar_sleeping, self.lbl_sleeping),
            ("Phone", self.bar_phone, self.lbl_phone),
            ("Absent", self.bar_absent, self.lbl_absent),
            ("Looked away", self.bar_gaze_away, self.lbl_gaze_away),
        ]

        start_row = 2
        for i, (label_text, bar, value_lbl) in enumerate(metric_rows):
            r = start_row + i
            grid.addWidget(make_label(label_text), r, 0)
            grid.addWidget(bar, r, 1)
            grid.addWidget(value_lbl, r, 2)

        # Make bars expand
        grid.setColumnStretch(1, 1)

        layout.addLayout(grid)
        layout.addStretch(1)

        self.set_summary(None)

    def set_summary(self, summary: Optional[Dict[str, Any]]):
        summary = summary or {}
        counts = summary.get("counts") or {}

        duration = summary.get("duration_seconds", 0.0)
        self.lbl_session_time.setText(_format_duration_hhmmss(duration))

        slept = _safe_int(counts.get(VisionEvents.SLEEPING, 0))
        phone = _safe_int(counts.get(VisionEvents.PHONE_DETECTED, 0))
        absent = _safe_int(counts.get(VisionEvents.ABSENT, 0))
        looked = _safe_int(counts.get(VisionEvents.GAZE_AWAY, 0))

        total_distractions = slept + phone + absent + looked
        self.kpi_value.setText(str(total_distractions))

        self.lbl_sleeping.setText(str(slept))
        self.lbl_phone.setText(str(phone))
        self.lbl_absent.setText(str(absent))
        self.lbl_gaze_away.setText(str(looked))

        focus_score = _compute_focus_score(slept, phone, absent, looked)
        self.lbl_focus_score.setText(f"{focus_score}/100")

        # Bars: scale to total, but keep a sane minimum so it's visible
        max_val = max(1, total_distractions, slept, phone, absent, looked)
        for bar, value in [
            (self.bar_sleeping, slept),
            (self.bar_phone, phone),
            (self.bar_absent, absent),
            (self.bar_gaze_away, looked),
        ]:
            bar.setRange(0, max_val)
            bar.setValue(value)


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

        self.personality_label = QLabel("PERSONALITY: -")
        self.personality_label.setStyleSheet(
            """
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: #00FF41;
            background: transparent;
            """
        )
        self.personality_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.personality_label, 0)

        self.image_label = QLabel("")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label, 2)

        self.insights_label = QLabel("")
        self.insights_label.setWordWrap(True)
        self.insights_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.insights_label.setStyleSheet(
            """
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: #7FFF00;
            background: transparent;
            """
        )
        layout.addWidget(self.insights_label, 0)

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
        self.personality_label.setText(f"PERSONALITY: {personality or '-'}")

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
            420,
            420,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def set_summary(self, summary: Optional[Dict[str, Any]]):
        summary = summary or {}
        counts = summary.get("counts") or {}

        slept = _safe_int(counts.get(VisionEvents.SLEEPING, 0))
        phone = _safe_int(counts.get(VisionEvents.PHONE_DETECTED, 0))
        absent = _safe_int(counts.get(VisionEvents.ABSENT, 0))
        looked = _safe_int(counts.get(VisionEvents.GAZE_AWAY, 0))

        insights = []
        if phone == 0:
            insights.append("• No phone detected.")
        else:
            insights.append(f"• Phone detected: {phone} time(s).")

        if looked == 0:
            insights.append("• No look-away events.")
        else:
            insights.append(f"• Looked away: {looked} time(s).")

        if absent == 0:
            insights.append("• No absence events.")
        else:
            insights.append(f"• Absent: {absent} time(s).")

        if slept == 0:
            insights.append("• No sleeping detected.")
        else:
            insights.append(f"• Slept: {slept} time(s).")

        # Keep it short (2-3 lines)
        self.insights_label.setText("\n".join(insights[:3]))

    def set_feedback_text(self, text: str):
        self.feedback_label.setText(text or "")

