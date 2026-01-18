import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                             QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from client.ui.name import personality_cards, voice_data
import client.ui.name as name

class BaseCard(QFrame):
    """카드 위젯의 공통 베이스 클래스"""
    # 클릭 이벤트를 부모에게 알리기 위한 시그널
    clicked = pyqtSignal(object)

    def __init__(self, icon, title, desc="", is_selected=False, card_class_name="BaseCard"):
        super().__init__()
        self.icon = icon
        self.title = title
        self.desc = desc
        self.is_selected = is_selected
        self.card_class_name = card_class_name  # 스타일시트에서 사용할 클래스 이름

        self.init_base_ui()
        self.update_style()

    def init_base_ui(self):
        """공통 UI 요소 초기화"""
        # 레이아웃 설정 (하위 클래스에서 오버라이드 가능)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(10, 30, 10, 10)  # 기본 마진 (하위 클래스에서 변경 가능)
        self.setLayout(layout)

        # 아이콘
        self.lbl_icon = QLabel(self.icon)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 32px; background: transparent;")
        
        # 제목
        self.lbl_title = QLabel(self.title)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0; margin-top: 10px; background: transparent;")

        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)

        # 마우스 커서를 손가락 모양으로 변경
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """클릭 이벤트 처리 - 공통 로직"""
        # 클릭 시 시그널 발생 (자신을 인자로 보냄)
        self.clicked.emit(self)
        super().mousePressEvent(event)
        
        # 하위 클래스에서 추가 처리를 위해 호출
        self.on_card_clicked()

    def on_card_clicked(self):
        """카드 클릭 시 호출되는 메서드 (하위 클래스에서 오버라이드)"""
        pass

    def set_selected(self, selected):
        """선택 상태 설정"""
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        """스타일 업데이트 - 공통 스타일 로직"""
        if self.is_selected:
            # 선택되었을 때: 붉은색 테두리 + 약간 붉은 틴트 배경
            self.setStyleSheet(f"""
                {self.card_class_name} {{
                    background-color: #2A1A1C; 
                    border: 2px solid #D64550;
                    border-radius: 15px;
                }}
            """)
        else:
            # 기본 상태: 어두운 회색 배경 + 연한 테두리
            self.setStyleSheet(f"""
                {self.card_class_name} {{
                    background-color: #1A1B1E;
                    border: 2px solid #333333;
                    border-radius: 15px;
                }}
                {self.card_class_name}:hover {{
                    border: 2px solid #555555;
                    background-color: #252629;
                }}
            """)

class PersonalityCard(BaseCard):
    """성격 선택 카드"""
    
    def __init__(self, icon, title, desc, is_selected=False):
        super().__init__(icon, title, desc, is_selected, card_class_name="PersonalityCard")
        # 설명 레이블 추가
        self.add_description()

    def add_description(self):
        """설명 레이블 추가"""
        layout = self.layout()
        self.lbl_desc = QLabel(self.desc)
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #A0A0A0; margin-top: 5px; background: transparent;")
        layout.addWidget(self.lbl_desc)

    def on_card_clicked(self):
        """카드 클릭 시 호출 - Personality 전용 처리"""
        # 클릭된 카드의 title을 name.py의 user_personality에 저장
        name.user_personality = self.title
        print(f"저장된 성격: {name.user_personality}")

class VoiceCard(BaseCard):
    """음성 선택 카드"""
    
    def __init__(self, title, desc="", is_selected=False):
        # VoiceCard는 icon이 고정되어 있음
        super().__init__("🔊", title, desc, is_selected, card_class_name="VoiceCard")
        # VoiceCard 전용 레이아웃 마진 설정
        layout = self.layout()
        layout.setContentsMargins(10, 10, 10, 10)  # 위아래 간격 10씩 고정
        # 크기 고정: 156 X 110
        self.setFixedSize(156, 110)

    def on_card_clicked(self):
        """카드 클릭 시 호출 - Voice 전용 처리"""
        # 클릭된 카드의 title을 name.py의 user_voice에 저장
        name.user_voice = self.title
        print(f"저장된 음성: {name.user_voice}")

class MainWindow(QMainWindow):
    # 세션 시작 시그널 (Key A) - 사용 안함 (Global Key로 대체됨)
    start_session_signal = pyqtSignal()
    # 디버그 윈도우 토글 시그널 (Key B) - 사용 안함 (Global Key로 대체됨)
    toggle_debug_signal = pyqtSignal()
    # 세션 토글 시그널 (Personality 화면에서 next 버튼 클릭 시 발생)
    toggle_session_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personality Selector Design")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("background-color: #121212;") # 전체 배경색

        # 메인 컨테이너
        container = QWidget()
        self.setCentralWidget(container)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(container)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 중앙 정렬
        
        # Voice 섹션 생성
        self.voice_section_widget = self.create_voice_section()
        main_layout.addWidget(self.voice_section_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Personality 섹션 생성
        self.personality_section_widget = self.create_personality_section()
        main_layout.addWidget(self.personality_section_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 화살표 네비게이션 버튼 생성
        self.nav_buttons_widget = self.create_navigation_buttons()
        main_layout.addWidget(self.nav_buttons_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 초기 화면: Voice 섹션만 보이기
        self.voice_section_widget.setVisible(True)
        self.personality_section_widget.setVisible(False)
        self.update_navigation_buttons()

    def create_voice_section(self):
        """Voice 선택 섹션 생성"""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 섹션 레이아웃 중앙 정렬
        
        # 섹션 제목 ("Voice")
        header = QLabel("Voice")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: white; font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        section_layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        # 그리드 레이아웃을 담을 위젯 생성
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15) # 카드 간 간격
        section_layout.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Voice 카드 데이터 (name.py에서 가져옴)
        self.voice_cards_data = voice_data
        self.voice_card_widgets = []

        # Voice 카드 생성 및 배치
        row = 0
        col = 0
        for idx, title in enumerate(self.voice_cards_data):
            # VoiceCard는 title만 있으므로 desc는 빈 문자열 사용
            card = VoiceCard(title, "", is_selected=False)
            card.clicked.connect(self.handle_voice_card_click) # 클릭 이벤트 연결
            
            grid_layout.addWidget(card, row, col)
            self.voice_card_widgets.append(card)

            col += 1
            if col > 3: # 4열 배치
                col = 0
                row += 1
        
        return section_widget

    def create_personality_section(self):
        """Personality 선택 섹션 생성"""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 섹션 레이아웃 중앙 정렬
        
        # 섹션 제목 ("Personality")
        header = QLabel("Personality")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: white; font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        section_layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)

        # 그리드 레이아웃을 담을 위젯 생성
        grid_widget = QWidget()
        self.personality_grid_layout = QGridLayout(grid_widget)
        self.personality_grid_layout.setSpacing(15) # 카드 간 간격
        section_layout.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Personality 카드 데이터 (name.py에서 가져옴)
        self.personality_cards_data = personality_cards
        self.personality_card_widgets = []

        # Personality 카드 생성 및 배치
        row = 0
        col = 0
        for idx, (icon, title, desc) in enumerate(self.personality_cards_data):
            card = PersonalityCard(icon, title, desc, is_selected=False)
            # 내용 영역 크기를 156 x 188로 고정 (테두리 2px 고려하여 전체 크기 160 x 192 설정)
            card.setFixedSize(160, 192)
            card.clicked.connect(self.handle_personality_card_click) # 클릭 이벤트 연결
            
            self.personality_grid_layout.addWidget(card, row, col)
            self.personality_card_widgets.append(card)

            col += 1
            if col > 3: # 4열 배치
                col = 0
                row += 1
        
        return section_widget

    def create_navigation_buttons(self):
        """화살표 네비게이션 버튼 생성"""
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 버튼 레이아웃 (가로 배치)
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)  # 버튼 간 간격
        
        # 이전 화면 버튼 (←)
        self.btn_prev = QPushButton("←")
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #1A1B1E;
                border: 2px solid #333333;
                border-radius: 10px;
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 60px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #252629;
                border: 2px solid #555555;
            }
            QPushButton:pressed {
                background-color: #2A1A1C;
                border: 2px solid #D64550;
            }
            QPushButton:disabled {
                background-color: #0F0F0F;
                border: 2px solid #1A1A1A;
                color: #555555;
            }
        """)
        self.btn_prev.clicked.connect(self.go_to_previous_screen)
        
        # 다음 화면 버튼 (→)
        self.btn_next = QPushButton("→")
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #1A1B1E;
                border: 2px solid #333333;
                border-radius: 10px;
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 60px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #252629;
                border: 2px solid #555555;
            }
            QPushButton:pressed {
                background-color: #2A1A1C;
                border: 2px solid #D64550;
            }
            QPushButton:disabled {
                background-color: #0F0F0F;
                border: 2px solid #1A1A1A;
                color: #555555;
            }
        """)
        self.btn_next.clicked.connect(self.go_to_next_screen)
        
        # 버튼을 가로로 배치
        button_layout.addWidget(self.btn_prev)
        button_layout.addWidget(self.btn_next)
        
        nav_layout.addLayout(button_layout)
        
        return nav_widget

    def update_navigation_buttons(self):
        """현재 화면에 따라 네비게이션 버튼 상태 업데이트"""
        # Voice 화면일 때
        if self.voice_section_widget.isVisible():
            self.btn_prev.setEnabled(False)  # 이전 화면 없음
            self.btn_next.setEnabled(True)   # 다음 화면 가능
        # Personality 화면일 때
        elif self.personality_section_widget.isVisible():
            self.btn_prev.setEnabled(True)   # 이전 화면 가능
            self.btn_next.setEnabled(True)   # 세션 시작 가능 (next 버튼으로 세션 시작)

    def go_to_previous_screen(self):
        """이전 화면으로 이동 (Personality → Voice)"""
        self.personality_section_widget.setVisible(False)
        self.voice_section_widget.setVisible(True)
        self.update_navigation_buttons()

    def go_to_next_screen(self):
        """다음 화면으로 이동 또는 세션 시작"""
        # Personality 화면이 켜져있는 경우
        if self.personality_section_widget.isVisible():
            # Personality 카드가 선택되어 있는지 확인
            selected_personality = None
            for card in self.personality_card_widgets:
                if card.is_selected:
                    selected_personality = card
                    break
            
            if selected_personality:
                # 세션 시작 시그널 발생
                self.toggle_session_signal.emit()
            else:
                # Personality 카드가 선택되지 않았으면 경고 메시지 표시
                print("성격을 먼저 선택해주세요.")
        # Voice 화면일 때
        else:
            # Voice 카드가 선택되어 있는지 확인
            selected_voice = None
            for card in self.voice_card_widgets:
                if card.is_selected:
                    selected_voice = card
                    break
            
            if selected_voice:
                self.voice_section_widget.setVisible(False)
                self.personality_section_widget.setVisible(True)
                self.update_navigation_buttons()
            else:
                # Voice 카드가 선택되지 않았으면 경고 메시지 표시
                print("음성을 먼저 선택해주세요.")

    def handle_voice_card_click(self, clicked_card):
        """Voice 카드 클릭 처리"""
        # 모든 Voice 카드의 선택 상태를 해제하고, 클릭된 카드만 선택 상태로 변경
        for card in self.voice_card_widgets:
            if card == clicked_card:
                card.set_selected(True)
            else:
                card.set_selected(False)
        
        # 음성만 저장하고 화면 전환은 하지 않음 (다음 버튼으로 전환)
        # 저장된 음성은 VoiceCard.on_card_clicked()에서 이미 처리됨

    def handle_personality_card_click(self, clicked_card):
        """Personality 카드 클릭 처리"""
        # 모든 Personality 카드의 선택 상태를 해제하고, 클릭된 카드만 선택 상태로 변경
        for card in self.personality_card_widgets:
            if card == clicked_card:
                card.set_selected(True)
            else:
                card.set_selected(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())