# client/ui/pipboy_detail_panel.py
"""
Pip-Boy 스타일 상세 정보 패널
우측 상세 정보 표시
"""

import os
import json
import time
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from client.ui.audio_visualizer import AudioVisualizer

# #region agent log helper (disabled in production)
def write_log(hypothesis_id, location, message, data=None):
    # Debug logging disabled - remove hardcoded paths for production
    pass
# #endregion

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
        self.current_tab = "VOICE"  # 현재 탭 추적
        self.init_ui()
        
        # 오디오 재생 관련
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        # 재생 시간 추적 타이머
        self.time_tracking_timer = QTimer(self)
        self.time_tracking_timer.timeout.connect(self._update_playback_time)
        self.time_tracking_timer.setInterval(50)  # 50ms마다 업데이트
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(5)  # 간격 최소화
        
        # 아이콘 또는 이미지 영역 (PERSONALITY 탭용)
        # VOICE 탭일 때는 오디오 시각화로 대체됨
        self.icon_container = QWidget()
        # 아이콘 컨테이너에 최소 높이 설정 (오디오 시각화가 보이도록)
        # 오디오 스펙트럼이 가득 차도록 최소 높이를 크게 설정
        self.icon_container.setMinimumHeight(400)
        icon_layout = QHBoxLayout(self.icon_container)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        self.icon_label = QLabel("")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            background: transparent;
        """)
        icon_layout.addWidget(self.icon_label)
        
        # 오디오 시각화 위젯 (VOICE 탭에서 아이콘 대신 표시)
        self.audio_visualizer = AudioVisualizer(self)
        # 초기에는 숨김 (VOICE 탭에서 아이템 선택 시 표시됨)
        self.audio_visualizer.setVisible(False)
        # 위젯이 레이아웃에서 공간을 차지하도록 설정 - 확장 가능하게
        from PyQt6.QtWidgets import QSizePolicy
        self.audio_visualizer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        icon_layout.addWidget(self.audio_visualizer, 1)  # stretch factor 1로 추가
        
        # 아이콘 레이블과 오디오 시각화는 동시에 표시되지 않도록
        # (레이아웃에 둘 다 추가되어 있지만 visible로 제어)
        
        layout.addWidget(self.icon_container)
        
        # 재생 버튼 (VOICE 탭에서만 표시) - 오디오 시각화 바로 아래에 배치
        self.play_button_container = QWidget()
        play_button_layout = QHBoxLayout(self.play_button_container)
        play_button_layout.setContentsMargins(0, 10, 0, 10)
        play_button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.play_button = QPushButton("PLAY")
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #00FF41;
                border: none;
                color: #000000;
                font-family: 'Courier New', monospace;
                font-size: 20px;
                font-weight: bold;
                padding: 10px 20px;
                min-width: 200px;
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
        self.play_button.clicked.connect(self.on_play_button_clicked)
        self.play_button.setVisible(False)
        
        play_button_layout.addWidget(self.play_button)
        layout.addWidget(self.play_button_container)
        
        # 상단 공간 확보 (오디오 시각화와 하단 정보 사이) - 더 많은 공간 확보
        layout.addStretch(2)  # stretch factor를 2로 증가
        
        # 제목 (녹색 배경 전체 영역) - 하단에 배치
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
        
        # 설명 - 하단에 배치
        self.desc_label = QLabel("Select an item from the list to view details.")
        self.desc_label.setStyleSheet("""
            font-family: 'JetBrains Mono', monospace;
            font-size: 18px;
            color: #00FF41;
            background: transparent;
        """)
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.desc_label)
        
    def _get_voice_description(self, voice_name):
        """보이스 이름에 해당하는 설명(대사) 반환"""
        voice_descriptions = {
            "Uncle Roger": "Don't use measuring spoon. We use feeling. Haiya",
            "Sportscaster": "GOAL!!!!!!! What a thunderbolt! It nearly ripped the back of the net off! An unbelievable strike!",
            "Shakespeare": "Even if the world ends tomorrow, I will still plant an apple tree today.",
            "Korean Mom": "ya! Why are you not studying yet. You hadn't finished homework yet!",
            "Gigachad": "I have no enemies. No one has enemies.",
            "Anime Girl": "Onii-chan, wake up! The sun is already high in the sky.",
            "Drill Sergeant": "My grandmother can do push-ups better than that, and she's been dead for twenty years!",
            "Gordon Ramsey": "it's a BLOODY DISASTER! The chicken is so raw, a skilled vet could still save it! GET OUT"
        }
        return voice_descriptions.get(voice_name, f"Details for {voice_name}")
    
    def set_item(self, item_text, item_desc="", icon=""):
        """아이템 정보 설정"""
        # VOICE 탭에서 다른 보이스로 변경 시 재생 중지
        is_voice_tab = (self.current_tab == "VOICE")
        if is_voice_tab and self.current_item and self.current_item != item_text:
            # 다른 보이스로 변경 중이면 재생 중지
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.stop()
                self.audio_visualizer.stop_visualization()
                self._stop_time_tracking()
        
        self.title_label.setText(item_text.upper())
        
        # VOICE 탭인 경우 보이스별 대사 사용, 아니면 전달받은 item_desc 사용
        if is_voice_tab:
            voice_desc = self._get_voice_description(item_text)
            self.desc_label.setText(voice_desc)
        elif item_desc:
            self.desc_label.setText(item_desc)
        else:
            self.desc_label.setText(f"Details for {item_text}")
        self.current_item = item_text
        
        if is_voice_tab:
            # VOICE 탭: 아이콘 숨기고 오디오 시각화 표시
            self.icon_label.setVisible(False)
            self.icon_container.setVisible(True)
            # 실제 보이스가 선택된 경우에만 오디오 시각화 표시
            # "VOICE SELECTION", "SELECT ITEM" 등은 무효한 선택으로 처리
            is_valid_voice = (item_text and 
                             item_text not in ["VOICE SELECTION", "SELECT ITEM", "PERSONALITY SELECTION"] and
                             item_text in ["Gordon Ramsey", "Gigachad", "Uncle Roger", "Anime Girl", 
                                         "Korean Mom", "Drill Sergeant", "Sportscaster", "Shakespeare"])
            if is_valid_voice:
                self.audio_visualizer.setVisible(True)
            else:
                self.audio_visualizer.setVisible(False)
        else:
            # PERSONALITY 탭: 오디오 시각화 숨기고 아이콘 표시
            self.audio_visualizer.setVisible(False)
            
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
                        self.icon_label.setVisible(True)
                        self.icon_container.setVisible(True)
                    else:
                        # 이미지 파일이 없으면 숨김
                        self.icon_label.setVisible(False)
                        self.icon_container.setVisible(False)
                else:
                    # 이모지나 텍스트 아이콘
                    self.icon_label.setText(icon)
                    self.icon_label.setStyleSheet("""
                        font-size: 64px;
                        color: #FFFF00;
                        background: transparent;
                    """)
                    self.icon_label.setVisible(True)
                    self.icon_container.setVisible(True)
            else:
                self.icon_label.setVisible(False)
                self.icon_container.setVisible(False)
        
        # VOICE 탭이고 음성이 선택된 경우에만 버튼 표시
        self.update_voice_controls_visibility()
    
    def set_current_tab(self, tab_name):
        """현재 탭 설정"""
        # 탭 변경 시 재생 중지 및 상태 리셋
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
            self.audio_visualizer.stop_visualization()
            self._stop_time_tracking()
        
        self.current_tab = tab_name
        
        # 탭 변경 시 current_item 초기화하여 이전 탭의 아이템 정보가 남지 않도록 함
        # 실제 아이템 선택은 load_voice_items() 또는 load_personality_items() 후에 set_item()으로 설정됨
        self.current_item = None
        
        # VOICE 탭으로 변경 시 오디오 시각화 숨김 (아이템이 선택되면 set_item에서 표시됨)
        if tab_name == "VOICE":
            self.icon_label.setVisible(False)
            self.icon_container.setVisible(True)
            self.audio_visualizer.setVisible(False)  # 초기에는 숨김
        else:
            # PERSONALITY 탭으로 변경 시 오디오 시각화 숨김
            self.audio_visualizer.setVisible(False)
        
        # 버튼 텍스트 업데이트 (탭 변경 시 항상 "PLAY"로)
        self.play_button.setText("PLAY")
        
        self.update_voice_controls_visibility()
    
    def update_voice_controls_visibility(self):
        """VOICE 탭에서만 버튼 표시 (시각화는 set_item에서 처리)"""
        is_voice_tab = (self.current_tab == "VOICE")
        # 실제 보이스가 선택되었는지 확인 (무효한 선택 메시지 제외)
        valid_voices = ["Gordon Ramsey", "Gigachad", "Uncle Roger", "Anime Girl", 
                       "Korean Mom", "Drill Sergeant", "Sportscaster", "Shakespeare"]
        has_voice_selected = (self.current_item is not None and 
                             self.current_item not in ["VOICE SELECTION", "SELECT ITEM", "PERSONALITY SELECTION"] and
                             self.current_item in valid_voices)
        
        show_controls = is_voice_tab and has_voice_selected
        
        # 재생 버튼만 표시/숨김 (오디오 시각화는 set_item에서 처리됨)
        self.play_button.setVisible(show_controls)
        
        # 버튼 텍스트 업데이트 (재생 상태에 따라)
        if show_controls:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.play_button.setText("STOP")
            else:
                self.play_button.setText("PLAY")
        else:
            # 버튼이 숨겨질 때는 항상 "PLAY"로 리셋
            self.play_button.setText("PLAY")
    
    def on_play_button_clicked(self):
        """재생 버튼 클릭 처리"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            # 재생 중이면 중지
            self.media_player.stop()
            self.audio_visualizer.stop_visualization()
            self.play_button.setText("PLAY")
        else:
            # 재생 시작
            self.play_voice_example()
    
    def _get_voice_audio_file(self, voice_name):
        """보이스 이름에 해당하는 오디오 파일 경로 반환"""
        # 보이스 이름 -> 파일명 매핑
        voice_file_mapping = {
            "Gordon Ramsey": "Gordon_Ramsay.mp3",
            "Gigachad": "Giga_Chad.mp3",
            "Uncle Roger": "Uncle_Roger.mp3",
            "Anime Girl": "Anime_girl.mp3",
            "Korean Mom": "K_mom.mp3",
            "Drill Sergeant": "Drill_Sergeant.mp3",
            "Sportscaster": "Football_Announce.mp3",
            "Shakespeare": "Poem.mp3"
        }
        
        audio_dir = os.path.join(os.path.dirname(__file__), "assets")
        filename = voice_file_mapping.get(voice_name, "voice_example.wav")
        audio_file = os.path.join(audio_dir, filename)
        
        # 파일이 없으면 기본 파일 사용
        if not os.path.exists(audio_file):
            audio_file = os.path.join(audio_dir, "voice_example.wav")
        
        return audio_file
    
    def play_voice_example(self):
        """음성 예시 재생"""
        # 현재 선택된 보이스에 맞는 오디오 파일 경로 가져오기
        if not self.current_item or self.current_item == "SELECT ITEM":
            print(f"[WARNING] No voice selected")
            return
        
        audio_file = self._get_voice_audio_file(self.current_item)
        
        if not os.path.exists(audio_file):
            print(f"[WARNING] Audio file not found: {audio_file}")
            # #region agent log
            write_log("B", "pipboy_detail_panel.py:308", "play_voice_example audio file not found", {"audio_file": audio_file})
            # #endregion
            return
        
        # 오디오 파일을 시각화 위젯에 로드 (스펙트럼 분석)
        # WAV와 MP3 모두 스펙트럼 분석 시도
        load_result = self.audio_visualizer.load_audio_file(audio_file)
        
        # #region agent log
        write_log("B", "pipboy_detail_panel.py:330", "play_voice_example load_audio_file result", {
            "load_result": load_result,
            "audio_file": audio_file,
            "file_ext": os.path.splitext(audio_file)[1],
            "audio_visualizer_visible": self.audio_visualizer.isVisible(),
            "audio_visualizer_size": (self.audio_visualizer.width(), self.audio_visualizer.height())
        })
        # #endregion
        
        # 오디오 파일 로드 및 재생
        url = QUrl.fromLocalFile(audio_file)
        self.media_player.setSource(url)
        self.media_player.play()
        self.play_button.setText("STOP")
        
        # 시각화 시작
        self.audio_visualizer.start_visualization()
        # #region agent log
        write_log("C", "pipboy_detail_panel.py:270", "play_voice_example start_visualization called", {
            "audio_visualizer_visible": self.audio_visualizer.isVisible(),
            "audio_visualizer_size": (self.audio_visualizer.width(), self.audio_visualizer.height())
        })
        # #endregion
        
        # 재생 시간 추적을 위한 타이머 시작
        self._start_time_tracking()
    
    def on_media_status_changed(self, status):
        """미디어 상태 변경 처리"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 재생 완료
            self.audio_visualizer.stop_visualization()
            self.play_button.setText("PLAY")
    
    def _start_time_tracking(self):
        """재생 시간 추적 시작"""
        if not self.time_tracking_timer.isActive():
            self.time_tracking_timer.start()
    
    def _stop_time_tracking(self):
        """재생 시간 추적 중지"""
        self.time_tracking_timer.stop()
    
    def _update_playback_time(self):
        """재생 시간 업데이트"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            position_ms = self.media_player.position()
            position_sec = position_ms / 1000.0
            self.audio_visualizer.set_current_time(position_sec)
            # #region agent log
            write_log("C", "pipboy_detail_panel.py:300", "_update_playback_time", {
                "position_sec": position_sec,
                "audio_visualizer_visible": self.audio_visualizer.isVisible()
            })
            # #endregion
    
    def on_playback_state_changed(self, state):
        """재생 상태 변경 처리"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            # 재생 시작 시 시간 추적 시작
            self._start_time_tracking()
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            # 재생 중지
            self._stop_time_tracking()
            self.audio_visualizer.stop_visualization()
            self.play_button.setText("PLAY")
        
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
