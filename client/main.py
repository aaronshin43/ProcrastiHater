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
from client.config import Config
from dotenv import load_dotenv
import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class GlobalKeyManager(QObject):
    """
    Global hotkey manager using the 'keyboard' library.
    Emits signals when registered hotkeys are pressed anywhere in the OS.
    """
    toggle_session_signal = pyqtSignal()
    toggle_debug_signal = pyqtSignal()
    toggle_pause_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # keyboard listeners run in a separate thread, so we accept that.
        # pyqtSignals are thread-safe when emitted from other threads.
        try:
            keyboard.add_hotkey('alt+a', self._on_session_toggle)
            keyboard.add_hotkey('alt+b', self._on_debug_toggle)
            keyboard.add_hotkey('alt+p', self._on_pause_toggle)
        except ImportError:
            print("❌ 'keyboard' library not found. Global hotkeys will not work.")
            print("   Please run: pip install keyboard")

    def _on_session_toggle(self):
        print("⌨️ Global Hotkey: Alt+A")
        self.toggle_session_signal.emit()

    def _on_debug_toggle(self):
        print("⌨️ Global Hotkey: Alt+B")
        self.toggle_debug_signal.emit()

    def _on_pause_toggle(self):
        print("⌨️ Global Hotkey: Alt+P")
        self.toggle_pause_signal.emit()

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
        vision_worker = VisionWorker(show_debug_window=True)
    except Exception as e:
        print(f"❌ Service Initialization Error: {e}")
        return

    # 4. UI 생성
    main_window = MainWindow()
    debug_window = DebugWindow()
    floating_widget = FloatingWidget()
    
    # Global Key Manager
    key_manager = GlobalKeyManager()

    # 5. 시그널 연결: 서비스 -> UI/네트워크
    # (1) VisionWorker 결과 -> LiveKitClient (서버로 데이터 전송)
    vision_worker.alert_signal.connect(livekit_client.send_packet)
    
    # (2) VisionWorker 프레임 -> DebugWindow (화면 표시)
    vision_worker.debug_frame_signal.connect(debug_window.update_image)

    # (3) LiveKit 상태 -> 로그 출력
    livekit_client.connected_signal.connect(lambda: print("✅ LiveKit Connected!"))
    livekit_client.disconnected_signal.connect(lambda: print("⚠️ LiveKit Disconnected."))
    livekit_client.error_signal.connect(lambda e: print(f"❌ LiveKit Error: {e}"))

    # 6. 시그널 연결: UI 제어 -> 서비스 제어
    def toggle_session():
        """Key A: 세션 시작/종료 토글"""
        if vision_worker.isRunning():
            print("🛑 Stopping Session triggered by Key A")
            # 세션 종료 로직
            vision_worker.stop()
            livekit_client.disconnect()
            
            # UI 상태 변경
            floating_widget.hide()
            debug_window.hide() # 세션 종료시 디버그 창도 닫음 (선택사항)
            main_window.show()
            print("   - Show Main Window, Hide Floating Widget")
        else:
            print("🚀 Starting Session triggered by Key A")
            # 세션 시작 로직
            print("   - Starting Vision Worker...")
            vision_worker.start()
            
            print("   - Connecting LiveKit...")
            livekit_client.connect()
            
            # UI 상태 변경
            main_window.hide()
            floating_widget.show()
            
            # 플로팅 위젯에 포커스를 줘서 키 입력을 받을 수 있게 함
            floating_widget.activateWindow()
            floating_widget.raise_()
            print("   - Hide Main Window, Show Floating Widget")

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
    key_manager.toggle_session_signal.connect(toggle_session)
    key_manager.toggle_debug_signal.connect(toggle_debug_window)
    key_manager.toggle_pause_signal.connect(toggle_pause)
    
    # MainWindow의 toggle_session_signal 연결 (Personality 화면에서 next 버튼 클릭 시)
    main_window.toggle_session_signal.connect(toggle_session)
    
    # FloatingWidget 우클릭 메뉴 시그널 연결
    def show_settings():
        """캐릭터 설정 창 표시"""
        main_window.show()
        main_window.activateWindow()
        main_window.raise_()
        print("   - Show Settings Window")
    
    def exit_application():
        """애플리케이션 종료"""
        print("🛑 Exit requested from Floating Widget menu")
        # 세션이 실행 중이면 종료
        if vision_worker.isRunning():
            vision_worker.stop()
            livekit_client.disconnect()
        # 앱 종료
        app.quit()
    
    floating_widget.show_settings_signal.connect(show_settings)
    floating_widget.pause_signal.connect(toggle_pause)
    floating_widget.exit_signal.connect(exit_application)

    # Legacy Local Connections (Optional: Keep default A/B in local windoes if desired, 
    # but user requested change to Alt+A/B globally, so we rely on key_manager priority)
    # main_window.start_session_signal.connect(toggle_session)
    # ...

    # 7. 초기 화면 표시
    print("✨ Client Ready. Press 'Alt+A' to start/stop session, 'Alt+B' to toggle debug view, 'Alt+P' to pause/resume.")
    main_window.show()

    # 8. 메인 루프 실행
    exit_code = app.exec()

    # 9. 종료 처리
    print("🛑 Stopping services...")
    # 비전 워커 종료
    if vision_worker.isRunning():
        vision_worker.stop()
        vision_worker.wait()
    
    # LiveKit 클라이언트 완전 종료 (루프 stop)
    if livekit_client:
        livekit_client.quit()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
