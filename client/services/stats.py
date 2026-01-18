import time
from collections import defaultdict
from shared.constants import ScreenEvents, VisionEvents, SystemEvents
from shared.protocol import Packet

# 통계 필터링용 키워드 (Agent와 유사하게 클라이언트 측 판단)
DISTRACTING_KEYWORDS = [
    "game", "steam", "riot", "league", "netflix", "twitch", "instagram", "twitter", "x.com", "facebook", "tiktok",
    "reddit", "disney", "hulu", "prime video", "battle.net", "epic games", "ubisoft", "origin", "blizzard",
    "minecraft", "roblox", "overwatch", "valorant", "pubg", "apex", "fifa", "nexon"
]

class SessionStats:
    """
    Records session statistics and distraction events for the Result Dashboard.
    Lives on the Client side to provide full history for the UI.
    """
    def __init__(self):
        # Cooldown to prevent counting the same event multiple times in a short burst (e.g. continuos detection)
        # Assuming Packet events are discrete triggers.
        self.last_event_time = defaultdict(float)
        self.cooldown = 5.0 # Seconds
        self.reset()

    def reset(self):
        """Reset all stats for a new session"""
        self.start_time = time.time()
        self.end_time = None
        self.events = [] # List of {"timestamp": float, "event": str, "data": dict}
        self.counts = defaultdict(int)
        self.last_event_time.clear()
        print("📊 Session Stats Reset")
    
    def is_distracting_window(self, packet: Packet) -> bool:
        """Check if a WINDOW_CHANGE packet is distracting based on keywords"""
        title = packet.data.get("window_title", "").lower()
        process = packet.data.get("process_name", "").lower()
        
        for kw in DISTRACTING_KEYWORDS:
            if kw in title or kw in process:
                return True
        return False

    def record_event(self, packet: Packet):
        """Record a distraction event"""
        now = time.time()
        event_type = packet.event
        
        # 0. 시스템 이벤트 등 통계에서 제외할 것들
        if event_type in [SystemEvents.SESSION_START, SystemEvents.PERSONALITY_UPDATE]:
            return

        # 1. WINDOW_CHANGE 필터링
        # 모든 창 전환을 기록하면 통계가 오염되므로, '딴짓'으로 의심되는 창만 기록
        if event_type == ScreenEvents.WINDOW_CHANGE:
            if not self.is_distracting_window(packet):
                return
            
            # 통계용 이벤트 이름 변경 (명확하게 구분하기 위함)
            # 예: "WINDOW_CHANGE" -> "Distracting App"
            # 카운팅 키를 별도로 쓸 수도 있지만, 여기선 event_type을 재정의해서 저장
            # (단, 원본 패킷은 건드리지 않음)
            # event_type = "Distracting App" # 이렇게 하면 UI에서 표시할 때 매핑 필요
            pass 

        # Simple debounce/cooldown logic
        if now - self.last_event_time[event_type] < self.cooldown:
            return

        self.last_event_time[event_type] = now
        self.counts[event_type] += 1
        
        # Add relative time from start
        relative_time = now - self.start_time
        
        event_record = {
            "timestamp": now,
            "relative_time": relative_time,
            "event": event_type,
            "data": packet.data
        }
        self.events.append(event_record)
        
        print(f"📊 Stat Recorded: {event_type} (Total: {self.counts[event_type]})")

    def stop_session(self):
        """Mark session end"""
        self.end_time = time.time()
        print(f"📊 Session Ended. Duration: {self.get_duration():.1f}s")
        print(f"📊 Summary: {dict(self.counts)}")
    
    def get_duration(self) -> float:
        """Get session duration in seconds"""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def get_summary(self):
        """Return a summary dictionary for the dashboard"""
        duration = self.get_duration()
        total_counts = sum(self.counts.values())
        
        # Calculate 'Focused Time' (Rough estimate: Total Duration - (Distractions * Penalty))
        # Or just return raw duration and let UI decide
        
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": duration,
            "total_distractions": total_counts,
            "counts": dict(self.counts),
            "history": self.events
        }
