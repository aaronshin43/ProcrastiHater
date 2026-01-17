import sys
import os
import asyncio
import time
from dotenv import load_dotenv

# 프로젝트 루트 경로를 sys.path에 추가하여 모듈 import 가능하게 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from agent.memory import AgentMemory
from agent.llm import LLMHandler
from agent.prompts import SYSTEM_PROMPT

# .env 파일 로드 (GOOGLE_API_KEY 확인용)
load_dotenv()

async def test_workflow():
    print("🧪 [테스트 시작] Private Watcher 핵심 로직 검증\n")

    # ==========================================
    # 1. Memory & Cooldown 테스트
    # ==========================================
    print("--- 1. Memory & Cooldown Test ---")
    # 테스트를 위해 쿨다운을 2초로 짧게 설정
    memory = AgentMemory(cooldown_seconds=2.0)
    
    test_events = [
        ("SLEEPING", {"confidence": 0.9}),
        ("SLEEPING", {"confidence": 0.8}),  # 바로 들어옴 -> 쿨다운 걸려야 함
        ("YOUTUBE",  {"title": "Funny Cats"}), # 다른 이벤트 -> 반응해야 함
    ]

    print(f"설정된 쿨다운: {memory.cooldown_seconds}초")
    
    for i, (evt_type, data) in enumerate(test_events):
        print(f"\n[Scenario {i+1}] 이벤트 발생: {evt_type}")
        
        # 1. 기억 저장
        memory.add_event(evt_type, data)
        
        # 2. 반응 여부 체크
        should_alert = memory.should_alert(evt_type)
        if should_alert:
            print(f"  => ✅ 알림 트리거 (LLM 호출)")
        else:
            print(f"  => 🥶 쿨다운 중 (무시)")
            
    # 강제로 시간 지연 후 재테스트
    print("\n... 2.5초 대기 중 ...")
    time.sleep(2.5)
    
    print("\n[Scenario 4] 시간 경과 후 재발생: SLEEPING")
    memory.add_event("SLEEPING", {"confidence": 0.95})
    if memory.should_alert("SLEEPING"):
        print(f"  => ✅ 알림 트리거 (쿨다운 해제됨)")
    else:
        print(f"  => ❌ 오류: 쿨다운이 풀리지 않음")

    print(f"\n[메모리 요약 확인]\n{memory.get_summary()}\n")

    # ==========================================
    # 2. LLM (Gemini) 연동 테스트
    # ==========================================
    print("--- 2. LLM (Gemini) Generation Test ---")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ [SKIP] .env 파일에 GOOGLE_API_KEY가 없습니다. LLM 테스트를 건너뜁니다.")
        return

    print(f"🔑 API Key 확인됨: {api_key[:5]}...")
    
    try:
        llm_handler = LLMHandler()
        
        # 가짜 상황 데이터 생성
        mock_context = f"""
        [현재 상황]
        - 이벤트: SLEEPING
        - 상세: {{'confidence': 0.99, 'state': 'eyes_closed'}}
        
        [기억 요약]
        {memory.get_summary()}
        """
        
        print("🤖 Gemini에게 잔소리 생성 요청 중...")
        start_time = time.time()
        
        response = await llm_handler.get_scolding(SYSTEM_PROMPT, mock_context)
        
        elapsed = time.time() - start_time
        print(f"\n🗣️ [Gemini 응답] ({elapsed:.2f}s)")
        print("=" * 40)
        print(response)
        print("=" * 40)
        
        if "오류" in response or len(response) == 0:
            print("❌ 테스트 실패: 응답이 이상합니다.")
        else:
            print("✅ 테스트 성공!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_workflow())
