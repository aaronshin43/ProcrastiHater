"""
Client Application Entry Point
-----------------------------
Orchestrates the Client Services (Vision, Network) and UI Windows (Main, Debug, Floating).
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# 프로젝트 루트 경로를 sys.path에 추가하여 모듈 import가 가능하게 함
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from client.ui.main_window import MainWindow
from client.ui.debug_window import DebugWindow
from client.ui.floating_widget import FloatingWidget
from client.services.vision import VisionWorker
from client.services.livekit_client import LiveKitClient
from client.services.screen import ScreenWorker # Import ScreenWorker
from client.services.stats import SessionStats
from client.config import Config
#from shared.context import * # Assuming... wait, better be explicit
from shared.protocol import Packet, PacketMeta
from shared.constants import SystemEvents, PacketCategory
from dotenv import load_dotenv
import keyboard
import time
from PyQt6.QtCore import QObject, pyqtSignal

class GlobalKeyManager(QObject):
    """
    Global hotkey manager using the 'keyboard' library.
    Emits signals when registered hotkeys are pressed anywhere in the OS.
    """
    toggle_session_signal = pyqtSignal()
    toggle_debug_signal = pyqtSignal()
    toggle_pause_signal = pyqtSignal()
    toggle_mic_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.last_mic_toggle_time = 0
        # keyboard listeners run in a separate thread, so we accept that.
        # pyqtSignals are thread-safe when emitted from other threads.
        try:
            # keyboard.add_hotkey('alt+a', self._on_session_toggle)
            keyboard.add_hotkey('alt+b', self._on_debug_toggle)
            # keyboard.add_hotkey('alt+p', self._on_pause_toggle)
            keyboard.add_hotkey('alt+s', self._on_mic_toggle)
        except ImportError:
            print("❌ 'keyboard' library not found. Global hotkeys will not work.")
            print("   Please run: pip install keyboard")

    def _on_session_toggle(self):
        print("⌨️ Global Hotkey: Alt+A (Disabled)")
        # self.toggle_session_signal.emit()

    def _on_debug_toggle(self):
        print("⌨️ Global Hotkey: Alt+B")
        self.toggle_debug_signal.emit()
    
    def _on_mic_toggle(self):
        # Simple debounce to prevent key repeat from toggling rapidly
        now = time.time()
        if now - self.last_mic_toggle_time < 0.3:
            return
        self.last_mic_toggle_time = now
        
        print("⌨️ Global Hotkey: Alt+S (Mic Toggle)")
        self.toggle_mic_signal.emit()

    def _on_pause_toggle(self):
        print("⌨️ Global Hotkey: Alt+P (Disabled)")
        # self.toggle_pause_signal.emit()

def main():
    # .env 로드
    load_dotenv(os.path.join(project_root, '.env'))

    # 1. 설정 검증
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please check your .env file.")
        return

    # 2. 애플리케이션 초기화
    app = QApplication(sys.argv)
    
    # 3. 서비스 인스턴스 생성 (아직 시작하지 않음)
    try:
        livekit_client = LiveKitClient()
        # show_debug_window=True: VisionWorker가 처리한 프레임을 시그널로 방출하게 함
        # 세션 통계 매니저 생성
        session_stats = SessionStats()
        vision_worker = VisionWorker(show_debug_window=True)
        # 스크린 워커 생성
        screen_worker = ScreenWorker()
    except Exception as e:
        print(f"❌ Service Initialization Error: {e}")
        return

    # 4. UI 생성
    main_window = MainWindow()
    debug_window = DebugWindow()
    floating_widget = FloatingWidget()
    
    # Global Key Manager
    key_manager = GlobalKeyManager()

    # Wrapper for conditional stats recording
    def record_stats_if_active(packet: Packet):
        if not livekit_client.is_paused():
            session_stats.record_event(packet)

    # 5. 시그널 연결: 서비스 -> UI/네트워크
    # (1-2) VisionWorker 결과 -> SessionStats (통계 저장)
    vision_worker.alert_signal.connect(record_stats_if_active)
    # (1) VisionWorker 결과 -> LiveKitClient (서버로 데이터 전송)
    vision_worker.alert_signal.connect(livekit_client.send_packet)
    
    # (1.5) ScreenWorker 결과 -> LiveKitClient 및 로그
    screen_worker.alert_signal.connect(record_stats_if_active)
    screen_worker.alert_signal.connect(livekit_client.send_packet)
    screen_worker.alert_signal.connect(lambda p: print(f"🖥️ Screen Event: {p.event} - {p.data.get('window_title','Unknown')}"))
    
    # (2) VisionWorker 프레임 -> DebugWindow (화면 표시)
    vision_worker.debug_frame_signal.connect(debug_window.update_image)

    # (3) LiveKit 상태 -> 로그 출력
    livekit_client.connected_signal.connect(lambda: print("✅ LiveKit Connected!"))
    livekit_client.disconnected_signal.connect(lambda: print("⚠️ LiveKit Disconnected."))
    livekit_client.error_signal.connect(lambda e: print(f"❌ LiveKit Error: {e}"))

    # 6. 시그널 연결: UI 제어 -> 서비스 제어
    import time
    last_toggle_time = 0
    TOGGLE_COOLDOWN = 1.0 # 1초 쿨다운

    def start_or_resume_session():
        """Confirm Button: 세션 시작 또는 설정 변경 후 재개"""
        nonlocal last_toggle_time
        current_time = time.time()
        
        if current_time - last_toggle_time < TOGGLE_COOLDOWN:
            print(f"⏳ Toggle Cooldown (Ignored): {current_time - last_toggle_time:.2f}s")
            return
        last_toggle_time = current_time

        if vision_worker.isRunning():
            # 이미 실행 중인 경우 -> 설정 변경 후 재개 (Unpause)
            print("🔄 Resuming Session (Unpausing)...")
            if livekit_client.is_paused():
                livekit_client.set_paused(False)
            
            # UI 상태 변경
            main_window.hide()
            floating_widget.show()
            floating_widget.activateWindow()
            floating_widget.raise_()
            print("   - Hide Main Window, Show Floating Widget")

        else:
            # 새로 시작하는 경우
            print("🚀 Starting New Session...")
            # 통계 리셋
            session_stats.reset()

            print("   - Starting Vision Worker...")
            vision_worker.start()
            
            print("   - Starting Screen Worker...")
            screen_worker.start()
            
            print("   - Connecting LiveKit...")
            livekit_client.connect()
            
            # 세션 시작 패킷 전송 (버퍼링됨)
            start_packet = Packet(
                event=SystemEvents.SESSION_START,
                data={},
                meta=PacketMeta(category=PacketCategory.SYSTEM)
            )
            livekit_client.send_packet(start_packet)

            # UI 상태 변경
            main_window.hide()
            floating_widget.show()
            
            # 플로팅 위젯에 포커스를 줘서 키 입력을 받을 수 있게 함
            floating_widget.activateWindow()
            floating_widget.raise_()
            print("   - Hide Main Window, Show Floating Widget")

    def stop_session_to_main_menu():
        """Quit Button: 세션 종료 후 메인 메뉴로 복귀"""
        print("🛑 Stopping Session -> Main Menu")
        
        # UI 상태 변경 (먼저 변경하여 반응성 확보)
        floating_widget.hide()
        debug_window.hide()
        main_window.show()
        main_window.activateWindow()
        main_window.raise_()
        
        # 서비스 종료
        if vision_worker.isRunning():
            vision_worker.stop()
        if screen_worker.isRunning():
            screen_worker.stop()
        
        if livekit_client.is_connected():
            livekit_client.disconnect()
        
        session_stats.stop_session()
        print("📊 Final Stats:", session_stats.get_summary())
        print("   - Show Main Window, Hide Floating Widget")

    def toggle_debug_window():
        """Key B: 디버그 윈도우 토글"""
        if debug_window.isVisible():
            debug_window.hide()
            print("   - Debug Window Hidden")
        else:
            debug_window.show()
            debug_window.activateWindow() # 포커스 이동
            debug_window.raise_()
            print("   - Debug Window Shown")

    def toggle_pause():
        """Key P: 일시중지 토글"""
        if not livekit_client.is_connected():
            print("⚠️ Session not running, cannot pause.")
            return

        current_state = livekit_client.is_paused()
        livekit_client.set_paused(not current_state)
        
        # UI 피드백 (예: 플로팅 위젯 투명도 변경 등)
        print(f"   - Session Paused: {not current_state}")

    # 모든 창에서 발생한 시그널을 동일한 핸들러에 연결 (어떤 창이 포커스되어 있든 키 동작)
    # Global Key Manager 연결
    # key_manager.toggle_session_signal.connect(toggle_session) # Disabled
    key_manager.toggle_debug_signal.connect(toggle_debug_window)
    key_manager.toggle_pause_signal.connect(toggle_pause)
    key_manager.toggle_mic_signal.connect(livekit_client.toggle_microphone)

    # 성격 변경 시그널 연결 (MainWindow -> LiveKitClient)
    main_window.personality_changed_signal.connect(livekit_client.send_packet)
    
    # MainWindow의 toggle_session_signal 연결 (Personality 화면에서 confirm 버튼 클릭 시)
    main_window.toggle_session_signal.connect(start_or_resume_session)
    
    # FloatingWidget 우클릭 메뉴 시그널 연결
    def show_settings():
        """캐릭터 설정 창 표시 (일시정지 후)"""
        if livekit_client.is_connected() and not livekit_client.is_paused():
            print("⏸️ Pausing Session for Settings...")
            livekit_client.set_paused(True)
            
        floating_widget.hide()
        main_window.show()
        main_window.activateWindow()
        main_window.raise_()
        print("   - Show Settings Window")
    
    # 설정: Pause session -> Open Main Window
    floating_widget.show_settings_signal.connect(show_settings)
    
    # 일시정지: Toggle Pause (화면 유지)
    floating_widget.pause_signal.connect(toggle_pause)
    
    # 종료: 세션 종료 -> 메인 메뉴 (앱 종료 아님)
    floating_widget.exit_signal.connect(stop_session_to_main_menu)

    # Legacy Local Connections (Optional: Keep default A/B in local windoes if desired, 
    # but user requested change to Alt+A/B globally, so we rely on key_manager priority)
    # main_window.start_session_signal.connect(toggle_session)
    # ...

    # 7. 초기 화면 표시
    print("✨ Client Ready. Press 'Alt+A' to start/stop session, 'Alt+B' to toggle debug view, 'Alt+P' to pause/resume, 'Alt+S' to talk.")
    main_window.show()

    # 8. 메인 루프 실행
    exit_code = app.exec()

    # 9. 종료 처리
    print("🛑 Stopping services...")
    # 비전 워커 종료
    if vision_worker.isRunning():
        vision_worker.stop()
        vision_worker.wait()
        
    if screen_worker.isRunning():
        screen_worker.stop()
        screen_worker.wait()
    
    # LiveKit 클라이언트 완전 종료 (루프 stop)
    if livekit_client:
        livekit_client.quit()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
