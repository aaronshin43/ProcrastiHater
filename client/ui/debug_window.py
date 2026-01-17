"""
디버그 윈도우 모듈
웹캠 영상을 실시간으로 표시하는 디버그용 GUI 창을 제공합니다.
PyQt6와 OpenCV를 사용하여 웹캠 영상을 별도 쓰레드에서 읽어 메인 윈도우에 표시합니다.
"""

import sys
import cv2
import numpy as np
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, Qt


# ============================================================================
# 1. 비디오 캡처 쓰레드 클래스
# ============================================================================
class VideoThread(QThread):
    """
    웹캠 영상을 별도 쓰레드에서 읽어오는 클래스
    메인 UI 쓰레드를 블로킹하지 않기 위해 별도 쓰레드에서 동작합니다.
    """
    
    # 영상 프레임을 전달할 시그널 (이미지 데이터 전송용)
    # np.ndarray 타입의 OpenCV 이미지 데이터를 전송합니다
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def run(self):
        """
        웹캠에서 프레임을 지속적으로 읽어 시그널로 전송합니다.
        프레임 40fps로 제한합니다.
        필요하다면 프레임 조절가능
        """
        # 웹캠 연결 (0번 카메라 디바이스)
        cap = cv2.VideoCapture(0)
        
        # ====================================================================
        # 프레임 레이트 제한 설정
        # ====================================================================
        # 목표 FPS: 초당 40프레임
        target_fps = 40
        # 프레임 간 최소 시간 간격 계산 (초 단위)
        # 1초 / 40fps = 0.025초 = 약 25ms
        frame_interval = 1.0 / target_fps
        
        # 이전 프레임 시간 기록 (초기값: 현재 시간)
        last_frame_time = time.time()
        
        # 무한 루프로 프레임을 지속적으로 읽어옴
        while True:
            # 현재 시간 기록
            current_time = time.time()
            
            # ret: 프레임 읽기 성공 여부 (True/False)
            # frame: 읽어온 프레임 데이터 (BGR 형식의 numpy 배열)
            ret, frame = cap.read()
            
            if ret:  # 프레임 읽기 성공 시
                # 프레임 간 경과 시간 계산
                elapsed_time = current_time - last_frame_time
                
                # 목표 프레임 간격보다 빠르게 읽었다면 대기
                if elapsed_time < frame_interval:
                    # 부족한 시간만큼 대기 (밀리초 단위)
                    sleep_time = (frame_interval - elapsed_time) * 1000
                    self.msleep(int(sleep_time))
                
                # 메인 쓰레드로 프레임 데이터 전달
                # 시그널을 통해 안전하게 UI 쓰레드로 데이터 전송
                self.change_pixmap_signal.emit(frame)
                
                # 현재 시간을 마지막 프레임 시간으로 업데이트
                last_frame_time = time.time()
        
        # 웹캠 리소스 해제 (현재 코드에서는 도달하지 않음)
        cap.release()


# ============================================================================
# 2. 메인 윈도우 클래스
# ============================================================================
class App(QMainWindow):
    """
    디버그 윈도우의 메인 윈도우 클래스
    웹캠 영상을 표시하는 GUI 창을 관리합니다.
    구성은 openvc 이미지 크기에 맞춰 웹캠을 띄우고, 이미지 크기와 같게 윈도우 크기를 설정
    """
    
    def __init__(self):
        """
        윈도우 초기화
        UI 구성 요소를 설정하고 비디오 쓰레드를 시작합니다.
        """
        super().__init__()
        
        # 윈도우 제목 설정
        self.setWindowTitle("PyQt 웹캠 출력 예제")
        
        # ====================================================================
        # UI 구성 요소 설정
        # ====================================================================
        # 영상을 표시할 라벨 위젯 생성
        self.label = QLabel(self)
        # 라벨을 중앙 위젯으로 설정 (윈도우 전체 영역 사용)
        self.setCentralWidget(self.label)
        
        # 윈도우 크기 초기화 플래그 (첫 프레임에서 윈도우 크기 설정용)
        self.window_size_set = False

        # ====================================================================
        # 비디오 쓰레드 설정 및 시작
        # ====================================================================
        # 비디오 캡처 쓰레드 인스턴스 생성
        self.thread = VideoThread()
        # 쓰레드의 시그널을 이미지 업데이트 메서드에 연결
        # 프레임이 전달될 때마다 update_image 메서드가 호출됨
        self.thread.change_pixmap_signal.connect(self.update_image)
        # 쓰레드 시작 (run 메서드 실행)
        self.thread.start()

    # ========================================================================
    # 3. 이미지 업데이트 메서드
    # ========================================================================
    def update_image(self, cv_img):
        """
        전달받은 OpenCV 프레임을 PyQt 형식으로 변환하여 화면에 업데이트
        
        Args:
            cv_img (np.ndarray): OpenCV로 읽어온 BGR 형식의 이미지 프레임
        """
        # ====================================================================
        # 색상 공간 변환: BGR -> RGB
        # ====================================================================
        # OpenCV는 BGR(Blue-Green-Red) 형식을 사용하지만,
        # PyQt는 RGB(Red-Green-Blue) 형식을 사용하므로 변환 필요
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        
        # 이미지 크기 정보 추출
        # h: 높이(height), w: 너비(width), ch: 채널 수(channels, RGB이므로 3)
        h, w, ch = rgb_image.shape
        
        # 한 줄당 바이트 수 계산 (이미지 데이터 포맷 변환에 필요)
        bytes_per_line = ch * w
        
        # ====================================================================
        # QImage 형식으로 변환
        # ====================================================================
        # numpy 배열 데이터를 QImage 객체로 변환
        # Format_RGB888: 8비트 RGB 형식 지정정
        # 이미지 변환 없이 그래돌 사용
        convert_to_Qt_format = QImage(
            rgb_image.data,      # 이미지 데이터 포인터
            w,                   # 너비
            h,                   # 높이
            bytes_per_line,      # 한 줄당 바이트 수
            QImage.Format.Format_RGB888  # RGB 888 형식
        )
        
        # ====================================================================
        # 이미지 원본 크기로 화면 출력
        # ====================================================================
        # 이미지 크기 조절 없이 원본 크기 그대로 사용
        p = QPixmap.fromImage(convert_to_Qt_format)
        
        # 라벨에 원본 크기 이미지 설정
        self.label.setPixmap(p)
        
        # ====================================================================
        # 윈도우 크기를 이미지 크기에 맞춰 설정 (첫 프레임에서만)
        # -> 이부분 코드는 윈도우 이미지를 openvc 이미지 크기에 맞춰 설정하는 코드
        # ====================================================================
        if not self.window_size_set:
            # 윈도우 크기를 이미지 크기에 맞춰 설정
            # 라벨 크기를 이미지 크기로 고정
            self.label.setFixedSize(w, h)
            # 윈도우 크기 조정 (이미지 크기 + 윈도우 프레임 크기 고려)
            self.resize(w, h)
            # 윈도우 크기 설정 완료 플래그
            self.window_size_set = True


# ============================================================================
# 4. 메인 실행부
# ============================================================================
if __name__ == "__main__":
    """
    프로그램 진입점
    애플리케이션을 초기화하고 메인 윈도우를 표시합니다.
    """
    # PyQt 애플리케이션 인스턴스 생성
    app = QApplication(sys.argv)
    
    # 메인 윈도우 인스턴스 생성
    a = App()
    
    # 윈도우 표시
    a.show()
    
    # 이벤트 루프 실행 및 종료 코드 반환
    sys.exit(app.exec())