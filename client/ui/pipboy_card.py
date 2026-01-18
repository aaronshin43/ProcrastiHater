# client/ui/pipboy_card.py
"""
Pip-Boy 스타일 카드 컴포넌트
CRT 화면 안의 UI 요소
"""

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QRect, QPoint, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient

class PipBoyCard(QFrame):
    """
    Pip-Boy 스타일 카드 - CRT 화면 안의 UI 요소
    """
    clicked = pyqtSignal(object)
    
    def __init__(self, icon, title, desc="", is_selected=False):
        super().__init__()
        self.icon = icon
        self.title = title
        self.desc = desc
        self.is_selected = is_selected
        self._hover_glow = 0.0
        
        self.init_ui()
        self.setup_animations()
    
    @pyqtProperty(float)
    def hover_glow(self):
        """호버 글로우 속성 (애니메이션용)"""
        return self._hover_glow
    
    @hover_glow.setter
    def hover_glow(self, value):
        """호버 글로우 속성 설정"""
        self._hover_glow = value
        self.update()  # repaint
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)
        
        # 아이콘 - 노란색, 글로우 효과
        self.lbl_icon = QLabel(self.icon)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet("""
            font-size: 48px;
            background: transparent;
            color: #FFFF00;
        """)
        
        # 제목 - 노란색, 굵게, 모노스페이스
        self.lbl_title = QLabel(self.title)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: bold;
            color: #FFFF00;
            background: transparent;
            margin-top: 12px;
        """)
        
        # 설명 - 녹색, 모노스페이스
        if self.desc:
            self.lbl_desc = QLabel(self.desc)
            self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_desc.setWordWrap(True)
            self.lbl_desc.setStyleSheet("""
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: #00FF41;
                background: transparent;
                margin-top: 8px;
            """)
            layout.addWidget(self.lbl_desc)
        
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(180, 220)
        
    def setup_animations(self):
        """애니메이션 설정"""
        # 호버 글로우 애니메이션
        self.glow_anim = QPropertyAnimation(self, b"hover_glow")
        self.glow_anim.setDuration(300)
        
    def enterEvent(self, event):
        """마우스 진입 시"""
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._hover_glow)
        self.glow_anim.setEndValue(1.0)
        self.glow_anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """마우스 이탈 시"""
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._hover_glow)
        self.glow_anim.setEndValue(0.0)
        self.glow_anim.start()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """클릭 이벤트"""
        self.clicked.emit(self)
        super().mousePressEvent(event)
        
    def set_selected(self, selected):
        """선택 상태 변경"""
        self.is_selected = selected
        self.update()
        
    def paintEvent(self, event):
        """커스텀 페인팅 - Pip-Boy 스타일"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        
        # 배경 - CRT 녹색
        bg_color = QColor(26, 77, 46, 200)  # 어두운 녹색
        if self.is_selected:
            bg_color = QColor(40, 100, 60, 240)  # 선택 시 밝게
        
        painter.fillRect(rect, bg_color)
        
        # 테두리 - 노란색 (선택 시) 또는 녹색 (기본)
        if self.is_selected:
            border_color = QColor(255, 255, 0)  # 노란색
            border_width = 3
        else:
            border_alpha = 100 + int(155 * self._hover_glow)
            border_color = QColor(0, 255, 65, border_alpha)  # 녹색
            border_width = 2
        
        pen = QPen(border_color)
        pen.setWidth(border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
        
        # 글로우 효과 (선택 시)
        if self.is_selected:
            for i in range(3):
                glow_alpha = 100 - i * 30
                glow_color = QColor(255, 255, 0, glow_alpha)
                glow_pen = QPen(glow_color)
                glow_pen.setWidth(2 + i)
                painter.setPen(glow_pen)
                painter.drawRect(rect.adjusted(-i, -i, i, i))
        
        # 내부 하이라이트 (상단) - 선택 시
        if self.is_selected:
            highlight = QLinearGradient(
                rect.topLeft(),
                QPoint(rect.left(), rect.top() + 20)
            )
            highlight.setColorAt(0.0, QColor(0, 255, 65, 50))
            highlight.setColorAt(1.0, QColor(0, 255, 65, 0))
            painter.setBrush(QBrush(highlight))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect.adjusted(0, 0, 0, -rect.height() + 20))
        
        super().paintEvent(event)
