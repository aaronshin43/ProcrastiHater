"""
Screen Monitoring Service 테스트 스크립트
활성 창 제목 추출 및 프로세스 감지 테스트

사용 방법:
    python test_screen.py

테스트 시나리오:
    1. 다른 창으로 전환하면 WINDOW_CHANGE 이벤트 발생
    2. 게임을 실행하면 GAMING 이벤트 발생
    3. 방해 앱(Netflix, YouTube 등)을 실행하면 DISTRACTING_APP 이벤트 발생
    4. Ctrl+C로 종료
"""

import sys
import os
from PyQt6.QtCore import QCoreApplication

# shared 폴더 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from shared.protocol import Packet
from client.services.screen import ScreenWorker

def on_alert(packet: Packet):
    """이벤트 수신 핸들러"""
    print(f"\n{'='*50}")
    print(f"📺 Screen Event: {packet.event}")
    print(f"📦 Data: {packet.data}")
    print(f"⏰ Timestamp: {packet.meta.timestamp}")
    print(f"  JSON: {packet.to_json()}\n")

def main():
    print("="*50)
    print("Screen Monitoring Service 테스트")
    print("="*50)
    print("다음 동작을 테스트하세요:")
    print("  1. 다른 창으로 전환하면 WINDOW_CHANGE 이벤트 발생")
    print("  2. 게임을 실행하면 GAMING 이벤트 발생")
    print("  3. 방해 앱(Netflix, YouTube 등)을 실행하면 DISTRACTING_APP 이벤트 발생")
    print("  4. Ctrl+C로 종료")
    print("="*50)
    
    # QApplication 생성 (QThread 사용을 위해 필요)
    app = QCoreApplication(sys.argv)
    
    # Screen Worker 생성 및 시작
    # check_interval 파라미터는 더 이상 사용되지 않지만 호환성을 위해 유지
    screen_worker = ScreenWorker(check_interval=2.0)
    screen_worker.alert_signal.connect(on_alert)
    
    print("\nScreen Worker 시작 중...")
    screen_worker.start()
    
    try:
        print("✅ Screen Worker 실행 중... (창 전환 및 앱 실행 테스트)")
        print("💡 창을 전환하거나 게임/방해 앱을 실행해보세요!\n")
        app.exec()
    except KeyboardInterrupt:
        print("\n\n⏹️  종료 신호 수신...")
    finally:
        screen_worker.stop()
        screen_worker.wait()
        print("✅ 테스트 종료")

if __name__ == "__main__":
    main()
