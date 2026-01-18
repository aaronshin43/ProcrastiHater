import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                             QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from client.ui.name import personality_cards, voice_data
from client.ui.pipboy_card import PipBoyCard
from client.ui.pipboy_status_bar import PipBoyStatusBar
from client.ui.pipboy_tab_bar import PipBoyTabBar
from client.ui.pipboy_list_item import PipBoyListItem
from client.ui.pipboy_detail_panel import PipBoyDetailPanel
from client.ui.crt_effects import CRTEffectsWidget
from client.ui.pipboy_design import get_crt_background_style, get_title_text_style
import client.ui.name as name

# shared 폴더 import (성격 변경 패킷 전송을 위해)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from shared.constants import SystemEvents, PacketCategory
from shared.protocol import Packet, PacketMeta

# shared 폴더 import (성격 변경 패킷 전송을 위해)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from shared.constants import SystemEvents, PacketCategory
from shared.protocol import Packet, PacketMeta

class ListPanelWidget(QWidget):
    """리스트 패널 위젯 - 녹색 테두리 박스"""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 배경 - 검정
        painter.fillRect(rect, QColor(0, 0, 0))
        
        # 녹색 실선 테두리 (상세 패널과 동일한 스타일: 10px 안쪽)
        border_rect = rect.adjusted(10, 10, -10, -10)
        pen = QPen(QColor(0, 255, 65), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(border_rect)
        
        super().paintEvent(event)

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
    # 성격 변경 시그널
    personality_changed_signal = pyqtSignal(Packet)
    # 세션 토글 시그널 (Personality 화면에서 next 버튼 클릭 시 발생)
    toggle_session_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProcrastiHator - Pip-Boy Edition")
        self.setGeometry(100, 100, 1200, 800)
        
        # Pip-Boy CRT 배경 스타일
        self.setStyleSheet(get_crt_background_style())

        # 메인 컨테이너
        container = QWidget()
        self.setCentralWidget(container)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Pip-Boy 상태 바 추가
        self.status_bar = PipBoyStatusBar()
        self.status_bar.setFixedHeight(50)
        main_layout.addWidget(self.status_bar)
        
        # 탭 바 추가
        self.tab_bar = PipBoyTabBar(["VOICE", "PERSONALITY"])
        self.tab_bar.tab_changed.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_bar)
        
        # CRT 화면 영역 (좌우 패널 구조)
        self.crt_screen_widget = QWidget()
        self.crt_screen_widget.setStyleSheet("background-color: #000000;")
        crt_layout = QHBoxLayout(self.crt_screen_widget)
        crt_layout.setContentsMargins(2, 2, 2, 2)  # 최소 여백
        crt_layout.setSpacing(2)  # 패널 간 최소 간격
        
        # 좌측 패널 (리스트) - 스크롤 가능 (녹색 테두리 박스)
        self.left_panel = ListPanelWidget()
        self.left_panel.setFixedWidth(320)  # 너비 약간 증가
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)  # 상세 패널과 동일한 마진
        left_layout.setSpacing(0)
        
        # 스크롤 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #000000;
            }
            QScrollBar:vertical {
                background-color: #000000;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #00FF41;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7FFF00;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 리스트 컨테이너
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)  # 마진 제거 (패널 마진 사용)
        self.list_layout.setSpacing(2)
        
        self.scroll_area.setWidget(self.list_container)
        left_layout.addWidget(self.scroll_area)
        
        crt_layout.addWidget(self.left_panel)
        
        # 우측 컨테이너 (상세 패널 + 버튼을 묶는 컨테이너)
        self.right_container = QWidget()
        self.right_container.setStyleSheet("background-color: #000000;")
        right_container_layout = QVBoxLayout(self.right_container)
        right_container_layout.setContentsMargins(0, 0, 0, 8)  # 아래쪽 마진 8px
        right_container_layout.setSpacing(2)  # 상세 패널과 버튼 사이 최소 간격
        
        # 상세 패널
        self.detail_panel = PipBoyDetailPanel()
        right_container_layout.addWidget(self.detail_panel)
        
        # 하단 버튼 영역
        # 상세 패널의 테두리(10px 안쪽)와 정렬되도록 마진 조정
        self.bottom_panel = QWidget()
        self.bottom_panel.setFixedHeight(60)
        self.bottom_panel.setStyleSheet("background-color: #000000;")
        bottom_layout = QHBoxLayout(self.bottom_panel)
        # 상세 패널의 테두리는 위젯 가장자리에서 10px 안쪽에 그려짐
        # 테두리와 정렬: 10px (좌우), 위아래는 최소화
        bottom_layout.setContentsMargins(10, 2, 10, 0)  # 좌우는 테두리와 정렬, 위는 최소, 아래는 0
        bottom_layout.setSpacing(0)
        
        self.btn_confirm = QPushButton("CONFIRM")
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #00FF41;
                border: none;
                color: #000000;
                font-family: 'Courier New', monospace;
                font-size: 16px;
                font-weight: bold;
                padding: 8px 0px;
            }
            QPushButton:hover {
                background-color: #7FFF00;
            }
            QPushButton:pressed {
                background-color: #FFFF00;
            }
            QPushButton:disabled {
                background-color: #000000;
                border: 2px solid #333333;
                color: #666666;
            }
        """)
        self.btn_confirm.clicked.connect(self.on_confirm_clicked)
        self.btn_confirm.setEnabled(False)  # 초기 상태는 비활성화
        
        # 버튼이 패널 전체를 채우도록 설정
        from PyQt6.QtWidgets import QSizePolicy
        self.btn_confirm.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        bottom_layout.addWidget(self.btn_confirm)
        
        # 하단 버튼을 오른쪽 컨테이너 레이아웃에 추가
        right_container_layout.addWidget(self.bottom_panel)
        
        crt_layout.addWidget(self.right_container, 1)
        
        # 오른쪽 컨테이너 높이를 왼쪽 패널 높이에 맞추기 (버튼이 왼쪽 패널 하단과 정렬되도록)
        # 레이아웃이 완료된 후 높이 동기화 (여러 시점에서 실행)
        def sync_heights():
            if self.left_panel.height() > 0 and self.left_panel.isVisible():
                # right_container 높이를 left_panel과 맞춤
                target_height = self.left_panel.height()
                self.right_container.setFixedHeight(target_height)
                
                # detail_panel 높이를 계산: right_container 높이 - 간격(2px) - bottom_panel 높이(60px)
                detail_panel_height = target_height - 2 - 60  # spacing(2) + bottom_panel(60)
                if detail_panel_height > 0:
                    self.detail_panel.setFixedHeight(detail_panel_height)
        
        from PyQt6.QtCore import QTimer
        # 여러 시점에서 높이 동기화
        QTimer.singleShot(100, sync_heights)
        QTimer.singleShot(300, sync_heights)
        QTimer.singleShot(500, sync_heights)
        # 윈도우 리사이즈 시에도 높이 동기화
        self.left_panel.installEventFilter(self)
        self.right_container.installEventFilter(self)
        
        main_layout.addWidget(self.crt_screen_widget, 1)
        
        # CRT 효과 오버레이 추가
        self.crt_effects = CRTEffectsWidget(self.crt_screen_widget)
        
        # 데이터 초기화
        self.voice_items = []
        self.personality_items = []
        self.current_selected_item = None
        self.current_tab = "VOICE"
        self.current_selected_index = -1  # 키보드 네비게이션용
        
        # 탭별 선택 상태 저장 (탭 이동 시에도 유지)
        self.selected_voice_item = None  # 선택된 Voice 아이템 이름
        self.selected_personality_item = None  # 선택된 Personality 아이템 이름
        
        # 초기 데이터 로드
        self.load_voice_items()
        
        # 키보드 포커스 설정
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # CRT 효과 위치 조정 (resize 이벤트에서)
        self.crt_screen_widget.installEventFilter(self)
        
        # 초기 CRT 효과 위치 설정
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.crt_effects.setGeometry(self.crt_screen_widget.rect()))
        
        self.update_confirm_button()
        self.update_status_bar()

    def clear_list_layout(self):
        """리스트 레이아웃 안전하게 초기화"""
        # 현재 탭에 맞는 아이템만 제거
        items_to_clear = self.voice_items if self.current_tab == "VOICE" else self.personality_items
        
        # 시그널 연결 해제만 수행 (선택 상태는 유지)
        for item in items_to_clear:
            try:
                if item:
                    item.clicked.disconnect()  # 시그널 연결 해제만
            except:
                pass
        
        # 레이아웃에서 모든 위젯 제거
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif child.spacerItem():
                self.list_layout.removeItem(child)
        
        # 현재 탭의 리스트만 초기화
        if self.current_tab == "VOICE":
            self.voice_items.clear()
        else:
            self.personality_items.clear()
        
    def load_voice_items(self):
        """Voice 아이템 로드"""
        # 기존 아이템 안전하게 제거
        self.clear_list_layout()
        
        # 새 아이템 생성
        for i, voice_name in enumerate(voice_data):
            # 이전에 선택된 항목인지 확인
            is_selected = (voice_name == self.selected_voice_item)
            
            item = PipBoyListItem(voice_name, icon="", is_selected=is_selected)
            # 람다 클로저 문제 해결: 기본값 사용
            item.clicked.connect(lambda clicked_item, name=voice_name: self.handle_voice_item_click(clicked_item, name))
            self.list_layout.addWidget(item)
            self.voice_items.append(item)
            
            # 이전에 선택된 항목이면 상태 복원
            if is_selected:
                self.current_selected_item = voice_name
                self.current_selected_index = i
                # 상세 정보도 복원
                self.detail_panel.set_item(voice_name, f"Voice: {voice_name}", icon="🔊")
        
        self.list_layout.addStretch()
        
        # 선택된 항목이 없으면 인덱스 초기화
        if self.current_selected_index < 0:
            self.current_selected_index = -1
        
        # 스크롤 위치 초기화
        self.scroll_area.verticalScrollBar().setValue(0)
        
    def load_personality_items(self):
        """Personality 아이템 로드"""
        # 기존 아이템 안전하게 제거
        self.clear_list_layout()
        
        # 새 아이템 생성
        for i, (icon, title, desc) in enumerate(personality_cards):
            # 이전에 선택된 항목인지 확인
            is_selected = (title == self.selected_personality_item)
            
            item = PipBoyListItem(title, icon=icon, is_selected=is_selected)
            # 람다 클로저 문제 해결: 기본값 사용
            item.clicked.connect(lambda clicked_item, t=title, d=desc, i=icon: self.handle_personality_item_click(clicked_item, t, d, i))
            self.list_layout.addWidget(item)
            self.personality_items.append(item)
            
            # 이전에 선택된 항목이면 상태 복원
            if is_selected:
                self.current_selected_item = title
                self.current_selected_index = i
                # 상세 정보도 복원
                self.detail_panel.set_item(title, desc, icon=icon)
        
        self.list_layout.addStretch()
        
        # 선택된 항목이 없으면 인덱스 초기화
        if self.current_selected_index < 0:
            self.current_selected_index = -1
        
        # 스크롤 위치 초기화
        self.scroll_area.verticalScrollBar().setValue(0)
        
    def on_tab_changed(self, tab_name):
        """탭 변경 처리"""
        # 탭 변경 시 선택 상태는 유지 (해제하지 않음)
        self.current_tab = tab_name
        
        # 현재 탭에 맞는 선택 상태로 전환
        if tab_name == "VOICE":
            self.current_selected_item = self.selected_voice_item
            self.load_voice_items()
            # 선택된 항목이 없으면 기본 메시지 표시
            if not self.selected_voice_item:
                self.detail_panel.set_item("VOICE SELECTION", "Select a voice from the list", icon="")
        elif tab_name == "PERSONALITY":
            self.current_selected_item = self.selected_personality_item
            self.load_personality_items()
            # 선택된 항목이 없으면 기본 메시지 표시
            if not self.selected_personality_item:
                self.detail_panel.set_item("PERSONALITY SELECTION", "Select a personality from the list", icon="")
        
        self.update_confirm_button()

    def update_confirm_button(self):
        """Voice와 Personality가 둘 다 선택되었는지 확인하고 Confirm 버튼 활성화"""
        # Voice와 Personality 둘 다 선택되었는지 확인
        both_selected = (self.selected_voice_item is not None and 
                        self.selected_personality_item is not None)
        self.btn_confirm.setEnabled(both_selected)
    
    def update_status_bar(self):
        """상태 바에 선택된 보이스와 성격 표시"""
        self.status_bar.update_selection(
            voice=self.selected_voice_item,
            personality=self.selected_personality_item
        )

    def on_confirm_clicked(self):
        """Confirm 버튼 클릭 처리 - 세션 시작"""
        # Voice와 Personality 둘 다 선택되었는지 다시 확인
        if self.selected_voice_item is None or self.selected_personality_item is None:
            return
        
        # 세션 시작 시그널 발생
        self.toggle_session_signal.emit()

    def handle_voice_item_click(self, clicked_item, voice_name):
        """Voice 아이템 클릭 처리"""
        if clicked_item is None:
            return
        
        # 모든 Voice 아이템의 선택 상태를 해제하고, 클릭된 아이템만 선택 상태로 변경
        for i, item in enumerate(self.voice_items):
            if item == clicked_item:
                item.set_selected(True)
                self.current_selected_item = voice_name
                self.current_selected_index = i
                # 탭별 선택 상태 저장
                self.selected_voice_item = voice_name
                # 음성 저장
                name.user_voice = voice_name
                print(f"[PIP-BOY] 저장된 음성: {name.user_voice}")
                # 상세 정보 업데이트
                self.detail_panel.set_item(voice_name, f"Voice: {voice_name}", icon="🔊")
                # 스크롤하여 선택된 아이템 보이게
                try:
                    self.scroll_to_item(item)
                except Exception as e:
                    print(f"[WARNING] 스크롤 실패: {e}")
            else:
                # 선택 해제 시 즉시 처리
                if item.is_selected:  # 현재 선택되어 있는 경우에만
                    item.set_selected(False)
                    item.repaint()
                    # 부모 위젯도 업데이트
                    if self.list_container:
                        self.list_container.update()
        
        self.update_confirm_button()
        self.update_status_bar()

    def handle_personality_item_click(self, clicked_item, title, desc, icon):
        """Personality 아이템 클릭 처리"""
        if clicked_item is None:
            return
        
        # 모든 Personality 아이템의 선택 상태를 해제하고, 클릭된 아이템만 선택 상태로 변경
        for i, item in enumerate(self.personality_items):
            if item == clicked_item:
                item.set_selected(True)
                self.current_selected_item = title
                self.current_selected_index = i
                # 탭별 선택 상태 저장
                self.selected_personality_item = title
                # 성격 저장
                name.user_personality = title
                print(f"[PIP-BOY] 저장된 성격: {name.user_personality}")

                # 성격 변경 패킷 생성 및 시그널 방출
                packet = Packet(
                    event=SystemEvents.PERSONALITY_UPDATE,
                    data={
                        "personality": title,
                        "description": desc
                    },
                    meta=PacketMeta(category=PacketCategory.SYSTEM)
                )
                self.personality_changed_signal.emit(packet)

                # 상세 정보 업데이트
                self.detail_panel.set_item(title, desc, icon=icon)
                # 스크롤하여 선택된 아이템 보이게
                try:
                    self.scroll_to_item(item)
                except Exception as e:
                    print(f"[WARNING] 스크롤 실패: {e}")
            else:
                # 선택 해제 시 즉시 처리
                if item.is_selected:  # 현재 선택되어 있는 경우에만
                    item.set_selected(False)
                    item.repaint()
                    # 부모 위젯도 업데이트
                    if self.list_container:
                        self.list_container.update()
        
        self.update_confirm_button()
        self.update_status_bar()
    
    def scroll_to_item(self, item):
        """아이템이 보이도록 스크롤"""
        try:
            if not item or not item.isVisible():
                return
            
            # 스크롤 영역에서 아이템 위치 계산
            item_pos = item.mapTo(self.list_container, item.rect().topLeft())
            scroll_value = self.scroll_area.verticalScrollBar().value()
            item_y = item_pos.y() + scroll_value
            
            # 아이템이 보이지 않으면 스크롤
            visible_top = scroll_value
            visible_bottom = scroll_value + self.scroll_area.viewport().height()
            
            if item_y < visible_top:
                # 위에 있으면 위로 스크롤
                self.scroll_area.verticalScrollBar().setValue(max(0, item_y - 10))
            elif item_y + item.height() > visible_bottom:
                # 아래에 있으면 아래로 스크롤
                self.scroll_area.verticalScrollBar().setValue(item_y + item.height() - self.scroll_area.viewport().height() + 10)
        except Exception as e:
            # 스크롤 실패 시 무시 (위젯이 삭제되었을 수 있음)
            pass
    
    def navigate_list(self, direction):
        """키보드 네비게이션"""
        current_items = self.voice_items if self.current_tab == "VOICE" else self.personality_items
        
        if not current_items:
            return
        
        # 현재 선택된 인덱스 찾기
        if self.current_selected_index < 0:
            # 선택된 아이템이 없으면 첫 번째 아이템 선택
            self.current_selected_index = 0
        else:
            # 방향에 따라 인덱스 변경
            self.current_selected_index = max(0, min(len(current_items) - 1, self.current_selected_index + direction))
        
        # 선택 변경
        for i, item in enumerate(current_items):
            try:
                if i == self.current_selected_index:
                    item.set_selected(True)
                    # 직접 핸들러 호출 (안전하게)
                    if self.current_tab == "VOICE":
                        # Voice 아이템의 경우
                        voice_name = item.text
                        self.handle_voice_item_click(item, voice_name)
                    else:
                        # Personality 아이템의 경우 아이콘과 설명 찾기
                        for icon, title, desc in personality_cards:
                            if title == item.text:
                                self.handle_personality_item_click(item, title, desc, icon)
                                break
                else:
                    # 선택 해제 시 즉시 처리
                    if item.is_selected:  # 현재 선택되어 있는 경우에만
                        item.set_selected(False)
                        item.repaint()
                        # 부모 위젯도 업데이트
                        if self.list_container:
                            self.list_container.update()
            except Exception as e:
                # 위젯이 삭제되었을 수 있음
                print(f"[WARNING] 네비게이션 오류: {e}")
                continue
    
    def keyPressEvent(self, event):
        """키보드 네비게이션"""
        if event.key() == Qt.Key.Key_Up:
            self.navigate_list(-1)  # 위로
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self.navigate_list(1)   # 아래로
            event.accept()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # 현재 선택된 아이템 클릭
            current_items = self.voice_items if self.current_tab == "VOICE" else self.personality_items
            if self.current_selected_index >= 0 and self.current_selected_index < len(current_items):
                current_items[self.current_selected_index].clicked.emit(current_items[self.current_selected_index])
            event.accept()
        elif event.key() == Qt.Key.Key_Left:
            # 이전 탭으로
            if self.current_tab == "PERSONALITY":
                self.tab_bar.set_current_tab("VOICE")
                self.on_tab_changed("VOICE")
            event.accept()
        elif event.key() == Qt.Key.Key_Right:
            # 다음 탭으로
            if self.current_tab == "VOICE":
                self.tab_bar.set_current_tab("PERSONALITY")
                self.on_tab_changed("PERSONALITY")
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def eventFilter(self, obj, event):
        """이벤트 필터 - CRT 효과 위치 조정 및 높이 동기화"""
        if obj == self.crt_screen_widget and event.type() == event.Type.Resize:
            # CRT 효과를 CRT 화면 위젯과 같은 크기로 조정
            self.crt_effects.setGeometry(self.crt_screen_widget.rect())
        elif obj == self.left_panel and event.type() == event.Type.Resize:
            # 왼쪽 패널 높이 변경 시 오른쪽 컨테이너와 detail_panel 높이 동기화
            if self.left_panel.height() > 0 and self.left_panel.isVisible():
                target_height = self.left_panel.height()
                self.right_container.setFixedHeight(target_height)
                # detail_panel 높이 계산: right_container 높이 - 간격(2px) - bottom_panel 높이(60px)
                detail_panel_height = target_height - 2 - 60
                if detail_panel_height > 0:
                    self.detail_panel.setFixedHeight(detail_panel_height)
        elif obj == self.right_container and event.type() == event.Type.Resize:
            # 오른쪽 컨테이너가 리사이즈될 때도 높이 재동기화
            if self.left_panel.height() > 0 and self.left_panel.isVisible():
                if self.right_container.height() != self.left_panel.height():
                    target_height = self.left_panel.height()
                    self.right_container.setFixedHeight(target_height)
                    detail_panel_height = target_height - 2 - 60
                    if detail_panel_height > 0:
                        self.detail_panel.setFixedHeight(detail_panel_height)
        return super().eventFilter(obj, event)
    
    def showEvent(self, event):
        """윈도우가 표시될 때 높이 동기화"""
        super().showEvent(event)
        # 윈도우가 표시된 후 높이 동기화
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._sync_heights)
    
    def _sync_heights(self):
        """높이 동기화 헬퍼 메서드"""
        if self.left_panel.height() > 0 and self.left_panel.isVisible():
            target_height = self.left_panel.height()
            self.right_container.setFixedHeight(target_height)
            # detail_panel 높이 계산: right_container 높이 - 간격(2px) - bottom_panel 높이(60px)
            detail_panel_height = target_height - 2 - 60
            if detail_panel_height > 0:
                self.detail_panel.setFixedHeight(detail_panel_height)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())