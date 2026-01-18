# client/ui/crt_effects.py
"""
CRT 효과 위젯 - 스캔라인, 노이즈, 스태틱 효과
"""

import random
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QColor

class CRTEffectsWidget(QWidget):
    """
    CRT 효과 오버레이 (스캔라인, 노이즈, 깜빡임)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanline_offset = 0
        self.noise_seed = 0
        
        # 노이즈 업데이트 타이머
        self.noise_timer = QTimer(self)
        self.noise_timer.timeout.connect(self.update_noise)
        self.noise_timer.start(100)  # 100ms마다 노이즈 업데이트
        
        # 스캔라인 애니메이션 타이머
        self.scanline_timer = QTimer(self)
        self.scanline_timer.timeout.connect(self.update_scanline)
        self.scanline_timer.start(16)  # 60fps
        
        # 투명 배경 설정
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
    def update_noise(self):
        """노이즈 시드 업데이트"""
        self.noise_seed = (self.noise_seed + 1) % 1000
        self.update()
        
    def update_scanline(self):
        """스캔라인 오프셋 업데이트"""
        self.scanline_offset = (self.scanline_offset + 1) % 100
        self.update()
        
    def paintEvent(self, event):
        """CRT 효과 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        rect = self.rect()
        
        # 스캔라인 (수평선) - CRT 모니터 느낌
        for y in range(0, self.height(), 3):
            # 사인파를 사용한 자연스러운 스캔라인
            alpha = 30 + 20 * abs(math.sin((y + self.scanline_offset) / 10))
            painter.fillRect(0, y, self.width(), 1, 
                           QColor(0, 0, 0, int(alpha)))
        
        # 필라인 (수직선) - 약하게
        for x in range(0, self.width(), 4):
            painter.fillRect(x, 0, 1, self.height(), 
                           QColor(0, 255, 65, 5))
        
        # 노이즈 (랜덤 픽셀) - CRT 노이즈 효과
        random.seed(self.noise_seed)
        noise_count = min(100, (self.width() * self.height()) // 500)
        
        for _ in range(noise_count):
            x = random.randint(0, self.width() - 1)
            y = random.randint(0, self.height() - 1)
            alpha = random.randint(10, 40)
            
            # 녹색 또는 노란색 노이즈
            color_choice = random.choice([
                QColor(0, 255, 65, alpha),   # 녹색
                QColor(255, 255, 0, alpha)  # 노란색
            ])
            
            size = random.randint(1, 2)
            painter.fillRect(x, y, size, size, color_choice)
        
        # 스태틱 효과 (가장자리) - 간헐적으로
        if random.random() < 0.1:  # 10% 확률
            static_count = random.randint(1, 3)
            for _ in range(static_count):
                static_x = random.randint(0, self.width() - 20)
                static_y = random.randint(0, self.height() - 20)
                static_size = random.randint(10, 30)
                static_alpha = random.randint(15, 30)
                
                static_rect = QRect(static_x, static_y, static_size, static_size)
                painter.fillRect(static_rect, 
                               QColor(255, 255, 0, static_alpha))
