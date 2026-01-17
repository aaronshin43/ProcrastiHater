import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                             QVBoxLayout, QFrame, QMainWindow)
from PyQt6.QtCore import Qt, pyqtSignal
from client.ui.name import personality_cards
import client.ui.name as name

class PersonalityCard(QFrame):
    # 클릭 이벤트를 부모에게 알리기 위한 시그널
    clicked = pyqtSignal(object)

    def __init__(self, icon, title, desc, is_selected=False):
        super().__init__()
        self.icon = icon
        self.title = title
        self.desc = desc
        self.is_selected = is_selected

        self.init_ui()
        self.update_style()

    def init_ui(self):
        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(10, 30, 10, 10)
        self.setLayout(layout)

        # 1. 아이콘 (이미지 대신 텍스트 이모지로 대체, 실제 구현시 QLabel에 QPixmap 사용 가능)
        self.lbl_icon = QLabel(self.icon)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 32px; background: transparent;")
        
        # 2. 제목
        self.lbl_title = QLabel(self.title)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0; margin-top: 10px; background: transparent;")

        # 3. 설명
        self.lbl_desc = QLabel(self.desc)
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #A0A0A0; margin-top: 5px; background: transparent;")

        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_desc)

        # 마우스 커서를 손가락 모양으로 변경
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    """
    클릭 이벤트 처리
    클릭된 카드의 정보를 저장한다.
    """
    def mousePressEvent(self, event):
        # 클릭 시 시그널 발생 (자신을 인자로 보냄)
        self.clicked.emit(self)
        super().mousePressEvent(event)
        
        # 클릭된 카드의 title을 name.py의 user_personality에 저장
        name.user_personality = self.title
        print(f"저장된 성격: {name.user_personality}")

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        # QSS(스타일시트)를 이용한 디자인 적용
        if self.is_selected:
            # 선택되었을 때: 붉은색 테두리 + 약간 붉은 틴트 배경
            self.setStyleSheet("""
                PersonalityCard {
                    background-color: #2A1A1C; 
                    border: 2px solid #D64550;
                    border-radius: 15px;
                }
            """)
        else:
            # 기본 상태: 어두운 회색 배경 + 연한 테두리
            self.setStyleSheet("""
                PersonalityCard {
                    background-color: #1A1B1E;
                    border: 2px solid #333333;
                    border-radius: 15px;
                }
                PersonalityCard:hover {
                    border: 2px solid #555555;
                    background-color: #252629;
                }
            """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personality Selector Design")
        self.setGeometry(100, 100, 1000, 500)
        self.setStyleSheet("background-color: #121212;") # 전체 배경색

        # 메인 컨테이너
        container = QWidget()
        self.setCentralWidget(container)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(container)
        
        # 섹션 제목 ("Personality")
        header = QLabel("Personality")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: white; font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(header)

        # 그리드 레이아웃을 담을 위젯 생성
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(15) # 카드 간 간격
        main_layout.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # 카드 데이터 (name.py에서 가져옴)
        self.cards_data = personality_cards

        self.card_widgets = []

        # 카드 생성 및 배치
        row = 0
        col = 0
        for idx, (icon, title, desc) in enumerate(self.cards_data):
            card = PersonalityCard(icon, title, desc, is_selected=False)
            # 내용 영역 크기를 156 x 188로 고정 (테두리 2px 고려하여 전체 크기 160 x 192 설정)
            card.setFixedSize(160, 192)
            card.clicked.connect(self.handle_card_click) # 클릭 이벤트 연결
            
            self.grid_layout.addWidget(card, row, col)
            self.card_widgets.append(card)

            col += 1
            if col > 3: # 4열 배치
                col = 0
                row += 1

    def handle_card_click(self, clicked_card):

        # 모든 카드의 선택 상태를 해제하고, 클릭된 카드만 선택 상태로 변경
        for card in self.card_widgets:
            if card == clicked_card:
                card.set_selected(True)
            else:
                card.set_selected(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())