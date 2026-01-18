# client/ui/pipboy_design.py
"""
Pip-Boy Retro CRT 디자인 시스템
Fallout Pip-Boy 스타일 컬러 팔레트 및 타이포그래피
"""

# 컬러 팔레트 (실제 Pip-Boy 참고)
PIPBOY_COLORS = {
    # 배경 - CRT 모니터 (검정 배경)
    "background": "#000000",        # 순수 검정
    "crt_screen": "#000000",        # 검정 배경
    "crt_dark": "#000000",          # 검정
    "crt_glow": "#00FF41",          # 밝은 녹색 (CRT 글로우)
    
    # 텍스트 (정확한 Pip-Boy 색상)
    "text_primary": "#00FF41",        # 녹색 (기본 텍스트) - 실제 Pip-Boy 녹색
    "text_secondary": "#7FFF00",     # 연한 녹색 (보조)
    "text_accent": "#FFFF00",         # 노란색 (강조/제목)
    "text_selected": "#000000",       # 검정 (선택된 아이템 텍스트)
    "text_warning": "#FF6B00",        # 주황 (경고)
    "text_error": "#FF0000",          # 빨강 (에러)
    
    # UI 요소
    "selection_bg": "#00FF41",       # 선택 배경 (완전 불투명 녹색)
    "hover_glow": "rgba(0, 255, 65, 0.3)",  # 호버 글로우
    "border": "#00FF41",              # 테두리 (녹색)
    
    # 효과
    "scanline": "rgba(0, 0, 0, 0.3)",  # 스캔라인
    "noise": "rgba(0, 255, 65, 0.1)",  # 노이즈
    "static": "rgba(255, 255, 0, 0.2)"  # 스태틱
}

# 타이포그래피
PIPBOY_TYPOGRAPHY = {
    "fontFamily": {
        "display": "'Courier New', 'Consolas', monospace",  # 디지털 폰트
        "mono": "'JetBrains Mono', 'Courier New', monospace",
        "label": "'Arial', sans-serif"  # 라벨용
    },
    
    "styles": {
        "title": {
            "font": "Courier New",
            "size": "24px",
            "weight": "bold",
            "color": "#FFFF00",  # 노란색
        },
        "data": {
            "font": "JetBrains Mono",
            "size": "14px",
            "color": "#00FF41",  # 녹색
        },
        "label": {
            "font": "Arial",
            "size": "12px",
            "color": "#7FFF00",  # 연한 녹색
        }
    }
}

# 스타일시트 템플릿
def get_crt_background_style():
    """CRT 배경 스타일 (검정 배경)"""
    return """
        background-color: #000000;
    """

def get_title_text_style():
    """제목 텍스트 스타일"""
    return """
        font-family: 'Courier New', monospace;
        font-size: 24px;
        font-weight: bold;
        color: #FFFF00;
        background: transparent;
        text-shadow: 0 0 10px #00FF41;
    """

def get_data_text_style():
    """데이터 텍스트 스타일"""
    return """
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        color: #00FF41;
        background: transparent;
    """

def get_label_text_style():
    """라벨 텍스트 스타일"""
    return """
        font-family: Arial, sans-serif;
        font-size: 12px;
        color: #7FFF00;
        background: transparent;
    """
