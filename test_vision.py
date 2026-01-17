"""
Vision Detection Service 테스트 스크립트
웹캠이 연결되어 있어야 합니다.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from client.services.vision import VisionWorker
from shared.protocol import Packet

def on_alert(packet: Packet):
    """알림 신호 수신 핸들러"""
    print(f"\n🚨 감지됨!")
    print(f"  Event: {packet.event}")
    print(f"  Category: {packet.meta.category}")
    print(f"  Timestamp: {packet.meta.timestamp}")
    print(f"  Data: {packet.data}")
    print(f"  JSON: {packet.to_json()}\n")

def main():
    print("=" * 50)
    print("Vision Detection Service 테스트")
    print("=" * 50)
    print("웹캠을 확인하고 다음 동작을 테스트하세요:")
    print("  1. 눈을 50초 이상 감고 있으면 SLEEPING 이벤트 발생")
    print("  2. 얼굴을 화면 밖으로 50초 이상 이동하면 ABSENT 이벤트 발생")
    print("  3. 시선을 다른 곳으로 50초 이상 돌리면 GAZE_AWAY 이벤트 발생")
    print("  4. 휴대폰을 카메라 앞에 보이면 즉시 PHONE_DETECTED 이벤트 발생")
    print("  5. 디버그 창에서 'q' 키를 누르면 종료")
    print("  6. Ctrl+C로 종료")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # VisionWorker 생성 (디버그 창 활성화)
    worker = VisionWorker(show_debug_window=True)
    worker.alert_signal.connect(on_alert)
    
    # 웹캠 연결 확인
    print("\n웹캠 연결 중...")
    worker.start()
    
    # 5초 후 상태 확인
    def check_status():
        if worker.isRunning():
            print("✅ Vision Worker 실행 중... (웹캠 확인 중)")
        else:
            print("❌ Vision Worker가 실행되지 않았습니다")
    
    QTimer.singleShot(5000, check_status)
    
    try:
        # 앱 실행
        app.exec()
    except KeyboardInterrupt:
        print("\n\n테스트 종료 중...")
    finally:
        worker.stop()
        worker.wait()
        print("✅ 테스트 종료")

if __name__ == "__main__":
    main()
