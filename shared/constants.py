# Event types for detection
class VisionEvents:
    """Vision detection events"""
    SLEEPING = "SLEEPING"  # 눈을 장시간 감고 있음 (졸음)
    ABSENT = "ABSENT"  # 얼굴이 화면에 감지되지 않음
    USER_RETURNED = "USER_RETURNED"  # 자리 비움 후 복귀
    GAZE_AWAY = "GAZE_AWAY"  # 시선을 다른 곳으로 돌림
    PHONE_DETECTED = "PHONE_DETECTED"  # 휴대폰 감지

class ScreenEvents:
    """Screen monitoring events"""
    GAMING = "GAMING"  # 게임 실행 중
    DISTRACTING_APP = "DISTRACTING_APP"  # 방해 앱 실행 중 (Netflix, YouTube 등)
    WINDOW_CHANGE = "WINDOW_CHANGE"  # 활성 창 변경

class SystemEvents:
    """System events"""
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"     # 세션 종료 요청 (Client -> Agent)
    SESSION_SUMMARY = "SESSION_SUMMARY" # 세션 요약 데이터 (Agent -> Client)
    PERSONALITY_UPDATE = "PERSONALITY_UPDATE" # 성격 변경 이벤트

# Packet categories
class PacketCategory:
    """Packet category types"""
    VISION = "VISION"
    SCREEN = "SCREEN"
    SYSTEM = "SYSTEM"
