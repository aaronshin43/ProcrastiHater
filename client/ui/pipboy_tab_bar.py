# client/ui/pipboy_tab_bar.py
"""
Pip-Boy 스타일 탭 바
상단 메인 탭 네비게이션
"""

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

class PipBoyTabBar(QWidget):
    """
    Pip-Boy 스타일 탭 바 - 상단 네비게이션
    """
    tab_changed = pyqtSignal(str)  # 탭 이름 전달
    
    def __init__(self, tabs=None, parent=None):
        super().__init__(parent)
        if tabs is None:
            tabs = ["VOICE", "PERSONALITY"]
        self.tabs = tabs
        self.current_tab = tabs[0] if tabs else None
        self.setFixedHeight(40)
        
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(30)
        
        self.tab_labels = {}
        
        for tab_name in self.tabs:
            tab_label = QLabel(tab_name)
            tab_label.setStyleSheet("""
                font-family: 'Courier New', monospace;
                font-size: 16px;
                font-weight: bold;
                color: #00FF41;
                background: transparent;
            """)
            tab_label.setCursor(Qt.CursorShape.PointingHandCursor)
            tab_label.mousePressEvent = lambda e, name=tab_name: self.on_tab_clicked(name)
            
            layout.addWidget(tab_label)
            self.tab_labels[tab_name] = tab_label
        
        layout.addStretch()  # 오른쪽 정렬을 위한 공간
        
    def on_tab_clicked(self, tab_name):
        """탭 클릭 처리"""
        if tab_name != self.current_tab:
            self.current_tab = tab_name
            self.update()
            self.tab_changed.emit(tab_name)
            
    def set_current_tab(self, tab_name):
        """현재 탭 설정"""
        self.current_tab = tab_name
        self.update()
        
    def paintEvent(self, event):
        """커스텀 페인팅 - 선택된 탭 밑줄 (브래킷 스타일)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 배경 - 검정
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # 선택된 탭 밑줄 그리기
        if self.current_tab and self.current_tab in self.tab_labels:
            tab_label = self.tab_labels[self.current_tab]
            tab_rect = tab_label.geometry()
            
            # 밑줄 (브래킷 스타일) - 더 정확한 Pip-Boy 스타일
            pen = QPen(QColor(0, 255, 65), 2)
            painter.setPen(pen)
            
            y_pos = tab_rect.bottom() - 2
            
            # 좌측 브래킷 [====
            painter.drawLine(tab_rect.left(), y_pos, 
                           tab_rect.left() + 8, y_pos)
            # 우측 브래킷 ====]
            painter.drawLine(tab_rect.right() - 8, y_pos,
                           tab_rect.right(), y_pos)
            # 중앙 밑줄
            painter.drawLine(tab_rect.left() + 8, y_pos,
                           tab_rect.right() - 8, y_pos)
        
        # 하단 구분선 (실선으로 변경)
        line_color = QColor(0, 255, 65, 200)
        pen = QPen(line_color, 1)
        painter.setPen(pen)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        
        super().paintEvent(event)
