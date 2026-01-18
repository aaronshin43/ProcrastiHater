import os
from typing import Any, Dict, Optional

from PyQt6.QtCore import QThread, pyqtSignal


class StatsFeedbackWorker(QThread):
    """
    Background Gemini call to generate stats feedback (English).

    Emits:
      - feedback_ready(request_id: int, text: str)
      - feedback_error(request_id: int, error: str)
    """

    feedback_ready = pyqtSignal(int, str)
    feedback_error = pyqtSignal(int, str)

    def __init__(self, request_id: int, personality: str, summary: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.request_id = int(request_id)
        self.personality = personality or ""
        self.summary = summary or {}

    def run(self):
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            self.feedback_error.emit(self.request_id, "GOOGLE_API_KEY not set. (LLM unavailable)")
            return

        try:
            from google import genai
            from google.genai import types
        except Exception as e:
            self.feedback_error.emit(self.request_id, f"google-genai import failed: {e}")
            return

        counts = (self.summary.get("counts") or {}) if isinstance(self.summary, dict) else {}
        duration_seconds = 0.0
        try:
            duration_seconds = float(self.summary.get("duration_seconds", 0.0))
        except Exception:
            duration_seconds = 0.0

        sleeping = counts.get("SLEEPING", 0)
        phone = counts.get("PHONE_DETECTED", 0)
        absent = counts.get("ABSENT", 0)
        gaze_away = counts.get("GAZE_AWAY", 0)

        # Keep it short, English, persona-flavored but not overly long.
        system_prompt = f"""
You are writing a short results feedback message in the voice of this character/personality: {self.personality}.
Language: English.
Length: 2 to 4 sentences max.
Goal: Give actionable feedback based on the stats. Be firm and motivating.
Do not mention API, models, or being an AI. Do not include bullet points.
"""

        user_prompt = f"""
Session summary:
- duration_seconds: {duration_seconds}
- sleeping_count: {sleeping}
- phone_count: {phone}
- absent_count: {absent}
- gaze_away_count: {gaze_away}

Write the feedback now.
"""

        try:
            client = genai.Client(api_key=api_key)

            # Safety settings: keep permissive but sane.
            safety_settings = [
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    safety_settings=safety_settings,
                ),
            )

            text = getattr(response, "text", "") or ""
            text = text.strip()
            if not text:
                self.feedback_error.emit(self.request_id, "Empty LLM response. (LLM unavailable)")
                return

            self.feedback_ready.emit(self.request_id, text)
        except Exception as e:
            self.feedback_error.emit(self.request_id, f"Gemini error: {e}")


def start_stats_feedback(request_id: int, personality: str, summary: Dict[str, Any], parent=None) -> StatsFeedbackWorker:
    """Convenience helper to create a worker; caller should connect signals and call start()."""
    return StatsFeedbackWorker(request_id=request_id, personality=personality, summary=summary, parent=parent)

