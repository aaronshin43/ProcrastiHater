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
    def __init__(self, history_limit: int = 5, cooldown_seconds: float = 10.0):
        """
        :param history_limit: 저장할 최근 이벤트 개수 (기본값: 5개)
        :param cooldown_seconds: 동일 이벤트에 대한 잔소리 최소 간격
        """
        self.history: deque = deque(maxlen=history_limit)
        self.last_alert_time: Dict[str, float] = {}
        self.violation_counts: Dict[str, int] = {}
        self.cooldown_seconds = cooldown_seconds

    def add_event(self, event_type: str, data: dict):
        """이벤트를 기억에 저장하고 카운트를 증가시킵니다."""
        # 쿨다운이 끝났을때(LLM이 호출되었을 때)만 저장하도록 로직 변경을 위해
        # 여기서는 단순히 카운트 증가와 히스토리 저장만 수행합니다.
        # 실제 호출 여부는 main.py에서 should_alert가 true일 때만 이 함수를 호출하도록 변경할 것입니다.
        
        self.history.append(EventLog(time.time(), event_type, data))
        
        if event_type not in self.violation_counts:
            self.violation_counts[event_type] = 0
        self.violation_counts[event_type] += 1

    def should_alert(self, event_type: str, cooldown_seconds: float = None) -> bool:
        """
        해당 이벤트에 대해 지금 반응(LLM 호출/TTS)해야 하는지 결정합니다.
        (쿨다운 체크)
        :param cooldown_seconds: 선택적 쿨다운 시간 오버라이드. 없으면 기본값 사용.
        """
        now = time.time()
        last_time = self.last_alert_time.get(event_type, 0)
        
        # 사용할 쿨다운 시간 결정 (인자 값 우선)
        effective_cooldown = cooldown_seconds if cooldown_seconds is not None else self.cooldown_seconds

        # 쿨다운 시간이 지나야만 True 반환
        if now - last_time > effective_cooldown:
            self.last_alert_time[event_type] = now
            return True
        
        return False

    def clear(self):
        """기억을 모두 초기화합니다 (새 세션 시작 시)."""
        self.history.clear()
        self.last_alert_time.clear()
        self.violation_counts.clear()

    def get_summary(self) -> str:
        """LLM 프롬프트에 주입할 최근 상태 요약본을 만듭니다."""
        if not self.history:
            return "아직 기록된 활동이 없습니다."

        summary_lines = ["최근 사용자 행동 기록 (최신순):"]
        
        # 최근 이벤트들을 역순으로 (최신이 먼저 오게)
        # 시간 차이(초)를 같이 표시해서 LLM이 시간 관계를 파악하기 쉽게 함
        now = time.time()
        for log in reversed(self.history):
            time_diff = int(now - log.timestamp)
            if time_diff < 60:
                time_str = f"{time_diff}초 전"
            else:
                time_str = f"{time_diff // 60}분 전"
            summary_lines.append(f"- [{time_str}] {log.event_type} (Context: {log.data})")

        summary_lines.append("\n누적 위반 횟수:")
        for evt, count in self.violation_counts.items():
            summary_lines.append(f"- {evt}: {count}회")

        return "\n".join(summary_lines)
