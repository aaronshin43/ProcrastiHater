# agent/memory.py
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class EventLog:
    timestamp: float
    event_type: str
    data: dict

class AgentMemory:
    def __init__(self, history_limit: int = 30, cooldown_seconds: float = 10.0):
        """
        :param history_limit: 저장할 최근 이벤트 개수
        :param cooldown_seconds: 동일 이벤트에 대한 잔소리 최소 간격
        """
        self.history: deque = deque(maxlen=history_limit)
        self.last_alert_time: Dict[str, float] = {}
        self.violation_counts: Dict[str, int] = {}
        self.cooldown_seconds = cooldown_seconds

    def add_event(self, event_type: str, data: dict):
        """이벤트를 기억에 저장하고 카운트를 증가시킵니다."""
        self.history.append(EventLog(time.time(), event_type, data))
        
        if event_type not in self.violation_counts:
            self.violation_counts[event_type] = 0
        self.violation_counts[event_type] += 1

    def should_alert(self, event_type: str) -> bool:
        """
        해당 이벤트에 대해 지금 반응(LLM 호출/TTS)해야 하는지 결정합니다.
        (쿨다운 체크)
        """
        now = time.time()
        last_time = self.last_alert_time.get(event_type, 0)

        # 쿨다운 시간이 지나야만 True 반환
        if now - last_time > self.cooldown_seconds:
            self.last_alert_time[event_type] = now
            return True
        
        return False

    def get_summary(self) -> str:
        """LLM 프롬프트에 주입할 최근 상태 요약본을 만듭니다."""
        if not self.history:
            return "아직 기록된 활동이 없습니다."

        summary_lines = ["최근 사용자 행동 기록:"]
        
        # 최근 5개 이벤트만 간략히
        recent_logs = list(self.history)[-5:]
        for log in recent_logs:
            time_str = time.strftime('%H:%M:%S', time.localtime(log.timestamp))
            summary_lines.append(f"- [{time_str}] {log.event_type}: {log.data}")

        summary_lines.append("\n누적 위반 횟수:")
        for evt, count in self.violation_counts.items():
            summary_lines.append(f"- {evt}: {count}회")

        return "\n".join(summary_lines)
