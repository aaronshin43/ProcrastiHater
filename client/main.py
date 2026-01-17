import sys
import os
from PyQt6.QtWidgets import QApplication

# 프로젝트 루트 경로를 sys.path에 추가하여 모듈 import가 가능하게 함
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from client.ui.main_window import MainWindow
from client.services.vision import VisionWorker
from client.services.livekit_client import LiveKitClient
from client.config import Config
from dotenv import load_dotenv

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
    
    # 3. 서비스 인스턴스 생성
    try:
        livekit_client = LiveKitClient()
        # show_debug_window=True로 하면 웹캠 화면과 분석 정보를 볼 수 있습니다.
        vision_worker = VisionWorker(show_debug_window=True)
    except Exception as e:
        print(f"❌ Service Initialization Error: {e}")
        return

    # 4. UI 생성
    window = MainWindow()

    # 5. 시그널 연결 (핵심 로직 연결)
    # VisionWorker가 감지한 이벤트(Packet)를 LiveKitClient를 통해 전송
    vision_worker.alert_signal.connect(livekit_client.send_packet)

    # 연결 상태 로그 출력
    livekit_client.connected_signal.connect(lambda: print("✅ LiveKit Connected!"))
    livekit_client.disconnected_signal.connect(lambda: print("⚠️ LiveKit Disconnected."))
    livekit_client.error_signal.connect(lambda e: print(f"❌ LiveKit Error: {e}"))

    # (선택) UI에서 Personality를 선택하면 알림을 주거나 할 수 있음
    # window.some_signal.connect(...)

    # 6. 서비스 시작
    print("🚀 Starting ProcrastiHator Client...")
    print("   - Vision Worker: Starting webcam...")
    vision_worker.start()
    
    print("   - LiveKit Client: Connecting...")
    livekit_client.connect()

    # UI 표시
    window.show()

    # 7. 메인 루프 실행
    exit_code = app.exec()

    # 8. 종료 처리
    print("🛑 Stopping services...")
    vision_worker.stop()
    vision_worker.wait()
    livekit_client.disconnect()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
