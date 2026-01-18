# client/ui/pipboy_status_bar.py
"""
Pip-Boy 스타일 상태 바
상단 정보 표시 (제목, 시간, 상태)
"""

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

class TitleMarkerWidget(QWidget):
    """제목 앞의 녹색 사각형 마커"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 배경 자동 채우기 활성화
        self.setAutoFillBackground(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # 배경을 먼저 검정색으로 채우기
        rect = self.rect()
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 녹색 사각형 그리기 (완전 불투명)
        painter.fillRect(rect, QColor(0, 255, 65))
        
        # super().paintEvent 호출하지 않음 (자식 위젯이 없으므로)

class PipBoyStatusBar(QWidget):
    """
    Pip-Boy 스타일 상태 바 - 상단 정보 표시
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        
        # 시간 업데이트 타이머
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 1초마다 업데이트
        
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 마진 제거
        layout.setSpacing(0)  # 간격 제거
        
        # 좌측: 제목
        self.title_label = QLabel("PROCRASTIHATOR")
        self.title_label.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: bold;
            color: #000000;
            background: transparent;
            padding: 10px 15px;
        """)
        
        # 중앙: 상태 (빈 공간으로 확장)
        self.status_label = QLabel("[READY]")
        self.status_label.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: bold;
            color: #000000;
            background: transparent;
            padding: 10px 15px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 우측: 시간
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 18px;
            font-weight: bold;
            color: #000000;
            background: transparent;
            padding: 10px 15px;
        """)
        self.update_time()  # 초기 시간 설정
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label, 1)  # 확장
        layout.addWidget(self.time_label)
        
    def update_time(self):
        """시간 업데이트"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)
        
    def set_status(self, status_text):
        """상태 텍스트 설정"""
        self.status_label.setText(f"[{status_text}]")
    
    def update_selection(self, voice=None, personality=None):
        """선택된 보이스와 성격을 표시"""
        if voice and personality:
            # 둘 다 선택된 경우
            self.status_label.setText(f"[READY] Voice: {voice} | Personality: {personality}")
        elif voice:
            # 보이스만 선택된 경우
            self.status_label.setText(f"[READY] Voice: {voice}")
        elif personality:
            # 성격만 선택된 경우
            self.status_label.setText(f"[READY] Personality: {personality}")
        else:
            # 아무것도 선택되지 않은 경우
            self.status_label.setText("[READY]")
        
    def paintEvent(self, event):
        """커스텀 페인팅 - 전체 녹색 배경 + 상단/하단 실선 구분선"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 배경 - 녹색 (전체 영역 채우기)
        painter.fillRect(rect, QColor(0, 255, 65))
        
        # 상단/하단 실선 구분선
        line_color = QColor(0, 0, 0, 100)  # 검정색 선 (녹색 배경 위에)
        pen = QPen(line_color, 2)
        painter.setPen(pen)
        
        # 상단 선
        painter.drawLine(0, 0, self.width(), 0)
        # 하단 선
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        
        super().paintEvent(event)
