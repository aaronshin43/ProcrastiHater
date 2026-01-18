# client/ui/floating_widget.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction

class FloatingWidget(QWidget):
    # 우클릭 메뉴 액션 시그널
    show_settings_signal = pyqtSignal()  # 캐릭터 설정
    pause_signal = pyqtSignal()  # 일시정지
    exit_signal = pyqtSignal()  # 종료
    
    def __init__(self):
        super().__init__()
        # 배경 투명하게 설정 (핵심)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        self.char_label = QLabel()
        
        # 이미지 로드 (멤버 3이 assets 폴더에 이미지 넣어야 함)
        pixmap = QPixmap("client/ui/assets/test.png")
        
        # 크기를 1/10로 줄이기
        if not pixmap.isNull():
            new_width = pixmap.width() // 10
            new_height = pixmap.height() // 10
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
        
        layout.addWidget(self.char_label)
        self.setLayout(layout)
        
        # 드래그를 위한 초기 위치 변수
        self.oldPos = None

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

    # Global Hotkey 사용으로 인해 로컬 keyPressEvent는 제거하거나 주석 처리해도 됨
    # 하지만 비상용으로 남겨둘 수도 있음 (현재는 Global Key가 우선이므로 제거하지 않음)

