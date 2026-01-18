# client/ui/pipboy_detail_panel.py
"""
Pip-Boy 스타일 상세 정보 패널
우측 상세 정보 표시
"""

import os
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap

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

class PipBoyDetailPanel(QWidget):
    """
    Pip-Boy 스타일 상세 정보 패널 - 우측 패널
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(5)  # 간격 최소화
        
        # 아이콘 또는 이미지 영역 (있는 경우)
        self.icon_container = QWidget()
        icon_layout = QHBoxLayout(self.icon_container)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label = QLabel("")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            background: transparent;
        """)
        icon_layout.addWidget(self.icon_label)
        layout.addWidget(self.icon_container)
        
        # 제목 (녹색 배경 전체 영역)
        title_container = QWidget()
        title_container.setStyleSheet("background-color: #00FF41;")  # 녹색 배경
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(12, 8, 12, 8)  # 패딩 추가
        title_layout.setSpacing(8)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.title_label = QLabel("SELECT ITEM")
        self.title_label.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 24px;
            font-weight: bold;
            color: #000000;
            background: transparent;
        """)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        layout.addWidget(title_container)
        
        # 구분선
        self.divider = QWidget()
        self.divider.setFixedHeight(2)
        layout.addWidget(self.divider)
        
        # 설명
        self.desc_label = QLabel("Select an item from the list to view details.")
        self.desc_label.setStyleSheet("""
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: #00FF41;
            background: transparent;
        """)
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.desc_label)
        
        layout.addStretch()
        
    def set_item(self, item_text, item_desc="", icon=""):
        """아이템 정보 설정"""
        self.title_label.setText(item_text.upper())
        
        if icon:
            # 이미지 파일인지 확인 (확장자로 판단)
            if icon.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # 이미지 파일 경로
                assets_dir = os.path.join(os.path.dirname(__file__), "assets")
                image_path = os.path.join(assets_dir, icon)
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    # 이미지 크기 조정 (상세 패널에 맞게 - 더 크게, 모든 이미지 동일한 크기)
                    scaled_pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.icon_label.setPixmap(scaled_pixmap)
                    self.icon_container.setVisible(True)
                else:
                    # 이미지 파일이 없으면 숨김
                    self.icon_container.setVisible(False)
            else:
                # 이모지나 텍스트 아이콘
                self.icon_label.setText(icon)
                self.icon_label.setStyleSheet("""
                    font-size: 64px;
                    color: #FFFF00;
                    background: transparent;
                """)
                self.icon_container.setVisible(True)
        else:
            self.icon_container.setVisible(False)
        
        if item_desc:
            self.desc_label.setText(item_desc)
        else:
            self.desc_label.setText(f"Details for {item_text}")
        self.current_item = item_text
        
    def paintEvent(self, event):
        """커스텀 페인팅 - 실선 테두리"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(10, 10, -10, -10)
        
        # 실선 테두리 (대시라인 제거)
        pen = QPen(QColor(0, 255, 65), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
        
        # 구분선 그리기 (실선으로 변경)
        if hasattr(self, 'divider'):
            divider_rect = self.divider.geometry()
            divider_pen = QPen(QColor(0, 255, 65, 100), 1)
            painter.setPen(divider_pen)
            painter.drawLine(divider_rect.left(), divider_rect.center().y(),
                           divider_rect.right(), divider_rect.center().y())
        
        super().paintEvent(event)
