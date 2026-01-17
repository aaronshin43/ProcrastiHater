import os
from google import genai
from google.genai import types

class LLMHandler:
    def __init__(self):
        # API 키 설정
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # 로컬 개발 편의를 위해 일단 경고만 하거나 에러를 발생시킴
            print("Error: GOOGLE_API_KEY environment variable not found.")
        
        # 클라이언트 초기화 (새로운 SDK 방식)
        self.client = genai.Client(api_key=api_key)
        
        # 안전 설정 (잔소리가 필터링되지 않도록 임계값을 모두 해제/낮춤)
        self.safety_settings = [
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE",
            ),
        ]

    async def get_scolding(self, system_prompt: str, user_context: str) -> str:
        """
        시스템 프롬프트와 사용자 상황 데이터를 받아 Gemini의 매운맛 반응을 반환합니다.
        """
        try:
            # 비동기 호출 (새로운 SDK 방식)
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_context,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    safety_settings=self.safety_settings
                )
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            # 에러 발생 시 기본 대사 반환 (Fail-safe)
            return "야! 시스템 오류났어! 빨리 안 고쳐?"
