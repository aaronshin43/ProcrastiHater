# client/ui/floating_widget.py
import os
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction
from . import name

class FloatingWidget(QWidget):
    # 우클릭 메뉴 액션 시그널
    show_settings_signal = pyqtSignal()  # 캐릭터 설정
    pause_signal = pyqtSignal()  # 일시정지
    exit_signal = pyqtSignal()  # 종료
    
    # Personality 이름 -> 이미지 파일명 매핑
    PERSONALITY_IMAGE_MAP = {
        "Gordon Ramsey": "gorden.png",
        "Gigachad": "chad.png",
        "Uncle Roger": "roger.png",
        "Anime Girl": "monika.png",
        "Korean Mom": "korea_mom.png",
        "Drill Sergeant": "surgeant.png",
        "Sportscaster": "caster.png",
        "Shakespeare": "poem.png"
    }
    
    def __init__(self):
        super().__init__()
        # 배경 투명하게 설정 (핵심)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        self.char_label = QLabel()
        
        # 초기 이미지 로드 (기본값 또는 personality 기반)
        self.update_image_from_personality()
        
        layout.addWidget(self.char_label)
        self.setLayout(layout)
        
        # 드래그를 위한 초기 위치 변수
        self.oldPos = None
    
    def update_image_from_personality(self):
        """선택된 personality에 따라 이미지를 업데이트"""
        # personality에 맞는 이미지 파일명 찾기
        personality = name.user_personality
        image_filename = self.PERSONALITY_IMAGE_MAP.get(personality, "test.png")
        
        # assets 폴더 경로
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        image_path = os.path.join(assets_dir, image_filename)
        
        # 이미지 파일이 없으면 기본 이미지 사용
        if not os.path.exists(image_path):
            image_path = os.path.join(assets_dir, "test.png")
        
        # 이미지 로드
        pixmap = QPixmap(image_path)
        
        # 크기를 1/12로 줄이기 (기존 1/10보다 작게)
        if not pixmap.isNull():
            new_width = pixmap.width() // 12
            new_height = pixmap.height() // 12
            # 0이 되면 안되므로 최소 1픽셀 보장
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            
            pixmap = pixmap.scaled(
                new_width, 
                new_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
        
        self.char_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        """마우스 클릭 시 위치 저장 또는 우클릭 메뉴 표시"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self.mousePressRight(event)

    def mouseMoveEvent(self, event):
        """마우스 이동 시 창 이동"""
        if self.oldPos and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def mousePressRight(self, event):
        """우클릭 시 설정 메뉴 표시"""
        menu = QMenu(self)
        
        # 캐릭터 설정 액션
        settings_action = QAction("캐릭터 설정", self)
        settings_action.triggered.connect(self.show_settings_signal.emit)
        menu.addAction(settings_action)
        
        # 일시정지 액션
        pause_action = QAction("일시정지", self)
        pause_action.triggered.connect(self.pause_signal.emit)
        menu.addAction(pause_action)
        
        # 구분선
        menu.addSeparator()
        
        # 종료 액션
        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.exit_signal.emit)
        menu.addAction(exit_action)
        
        # 메뉴를 마우스 위치에 표시
        menu.exec(event.globalPosition().toPoint())

    def set_angry(self):
        # TODO: 화난 이미지로 변경하는 함수
        pass

