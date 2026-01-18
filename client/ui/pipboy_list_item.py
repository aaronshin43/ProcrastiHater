# client/ui/pipboy_list_item.py
"""
Pip-Boy 스타일 리스트 아이템
실제 Pip-Boy UI의 좌측 리스트 아이템
"""

import os
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap

class BulletMarkerWidget(QWidget):
    """리스트 아이템의 녹색 사각형 불릿 마커"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(0, 255, 65)
        self._is_visible = False  # 기본적으로 숨김
        # 배경 자동 채우기 활성화
        self.setAutoFillBackground(True)
        
    def set_color(self, color):
        """색상 설정"""
        self._color = color
        self.update()
        
    def set_visible(self, visible):
        """가시성 설정 (공간은 유지)"""
        self._is_visible = visible
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        rect = self.rect()
        
        # 배경을 먼저 검정색으로 채우기 (항상 공간 유지)
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 가시성이 True일 때만 사각형 그리기
        if self._is_visible:
            painter.fillRect(rect, self._color)
        
        # super().paintEvent 호출하지 않음 (자식 위젯이 없으므로)

class PipBoyListItem(QWidget):
    """
    Pip-Boy 스타일 리스트 아이템 - 좌측 패널용
    """
    clicked = pyqtSignal(object)
    
    def __init__(self, text, icon="", is_selected=False):
        super().__init__()
        self.text = text
        self.icon = icon
        self.is_selected = is_selected
        self._hover_glow = 0.0
        self.setFixedHeight(50)  # 이미지 크기 증가에 맞춰 높이 증가
        
        # 불투명 페인팅 강제 (배경이 확실히 지워지도록)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        self.init_ui()
        self.setup_animations()
        
    def setup_animations(self):
        """애니메이션 설정"""
        self.glow_anim = QPropertyAnimation(self, b"hover_glow")
        self.glow_anim.setDuration(200)
        
    @pyqtProperty(float)
    def hover_glow(self):
        return self._hover_glow
    
    @hover_glow.setter
    def hover_glow(self, value):
        self._hover_glow = value
        self.update()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)
        
        # 아이콘 또는 이미지 (있는 경우)
        if self.icon:
            self.icon_label = QLabel()
            # 이미지 파일인지 확인 (확장자로 판단)
            if self.icon.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # 이미지 파일 경로
                assets_dir = os.path.join(os.path.dirname(__file__), "assets")
                image_path = os.path.join(assets_dir, self.icon)
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    # 이미지 크기 조정 (리스트 아이템에 맞게 - 더 크게)
                    scaled_pixmap = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.icon_label.setPixmap(scaled_pixmap)
                else:
                    # 이미지 파일이 없으면 텍스트로 표시
                    self.icon_label.setText("?")
                    self.icon_label.setStyleSheet("""
                        font-size: 16px;
                        color: #FFFF00;
                        background: transparent;
                    """)
            else:
                # 이모지나 텍스트 아이콘
                self.icon_label.setText(self.icon)
                self.icon_label.setStyleSheet("""
                    font-size: 16px;
                    color: #FFFF00;
                    background: transparent;
                """)
            self.icon_label.setFixedWidth(60)
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.icon_label)
        
        # 불릿 포인트 (녹색 사각형 - 커스텀 위젯)
        # 항상 공간은 유지하되, 선택되었을 때만 표시
        self.bullet = BulletMarkerWidget()
        self.bullet.setFixedSize(8, 8)
        # 항상 위젯은 보이지만, 내용은 선택 상태에 따라 표시
        self.bullet.set_visible(self.is_selected)
        
        # 텍스트
        self.text_label = QLabel(self.text)
        self.update_text_style()
        
        layout.addWidget(self.bullet)
        layout.addWidget(self.text_label, 1)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def update_text_style(self):
        """텍스트 스타일 업데이트"""
        if self.is_selected:
            # 선택 시: 검정 텍스트
            self.text_label.setStyleSheet("""
                font-family: 'Courier New', monospace;
                font-size: 20px;
                color: #000000;
                background: transparent;
            """)
            # 불릿 마커 표시 (검정색)
            self.bullet.set_visible(True)
            self.bullet.set_color(QColor(0, 0, 0))
        else:
            # 기본: 녹색 텍스트
            self.text_label.setStyleSheet("""
                font-family: 'Courier New', monospace;
                font-size: 20px;
                color: #00FF41;
                background: transparent;
            """)
            # 불릿 마커 숨김 (공간은 유지)
            self.bullet.set_visible(False)
        
    def enterEvent(self, event):
        """마우스 진입 시"""
        if not self.is_selected:
            self.glow_anim.stop()
            self.glow_anim.setStartValue(self._hover_glow)
            self.glow_anim.setEndValue(1.0)
            self.glow_anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """마우스 이탈 시"""
        if not self.is_selected:
            self.glow_anim.stop()
            self.glow_anim.setStartValue(self._hover_glow)
            self.glow_anim.setEndValue(0.0)
            self.glow_anim.start()
        super().leaveEvent(event)
        
    def set_selected(self, selected):
        """선택 상태 변경"""
        old_selected = self.is_selected
        self.is_selected = selected
        self.update_text_style()
        
        # 선택 해제 시 호버 글로우도 리셋
        if not selected:
            self.glow_anim.stop()
            self._hover_glow = 0.0
        
        # 선택 상태가 변경되면 즉시 다시 그리기
        if old_selected != selected:
            # 강제로 다시 그리기
            self.update()
            self.repaint()
            # 부모 위젯에도 업데이트 요청
            if self.parent():
                self.parent().update()
        
    def mousePressEvent(self, event):
        """클릭 이벤트"""
        self.clicked.emit(self)
        super().mousePressEvent(event)
        
    def paintEvent(self, event):
        """커스텀 페인팅 - 선택 시 완전 불투명 녹색 배경"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # 픽셀 퍼펙트
        
        rect = self.rect()
        
        # 배경을 먼저 완전히 지움 (검정색) - 항상 먼저 그리기
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 선택 시: 완전 불투명 녹색 배경
        if self.is_selected:
            painter.fillRect(rect, QColor(0, 255, 65))  # 완전 불투명
        # 호버 시: 약간의 글로우 (선택되지 않고 호버 중인 경우에만)
        elif not self.is_selected and self._hover_glow > 0:
            glow_alpha = int(30 * self._hover_glow)
            painter.fillRect(rect, QColor(0, 255, 65, glow_alpha))
        # 선택되지 않고 호버도 아닌 경우: 검정 배경만 (이미 위에서 그렸음)
        
        # 자식 위젯들을 그리기
        super().paintEvent(event)
