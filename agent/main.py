# agent/main.py
import asyncio
import logging
import sys, os
from dotenv import load_dotenv

load_dotenv()

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, tts
from livekit.plugins import elevenlabs

# shared 폴더 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.protocol import Packet
from agent.memory import AgentMemory
from agent.prompts import SYSTEM_PROMPT
from agent.llm import LLMHandler

logger = logging.getLogger("procrastihator")

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    print("🤖 에이전트가 방에 입장했습니다.")
    
    # 1. 모듈 초기화
    memory = AgentMemory(cooldown_seconds=10.0)
    llm_handler = LLMHandler()
    
    # 2. TTS 초기화
    # 환경변수에서 키를 찾고, 없으면 경고
    tts_api_key = os.getenv("ELEVEN_API_KEY")
    if not tts_api_key:
        logger.warning("⚠️ ELEVENLABS_API_KEY not found. TTS might fail.")
        
    tts_plugin = elevenlabs.TTS(api_key=tts_api_key)

    # 3. Audio Track 변수 (첫 오디오 데이터 수신 시 초기화)
    audio_source = None
    audio_track = None

    async def scold_user(packet: Packet):
        nonlocal audio_source, audio_track
        logger.info(f"⚡ 처형 프로세스 시작: {packet.event}")

        # A. 문맥 생성
        context_str = f"""
        [현재 상황]
        - 이벤트: {packet.event}
        - 상세: {packet.data}
        
        [기억 요약]
        {memory.get_summary()}
        """

        # B. LLM 멘트 생성
        try:
            text = await llm_handler.get_scolding(SYSTEM_PROMPT, context_str)
            logger.info(f"🗣️ 생성된 잔소리: {text}")
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return

        # C. TTS 송출
        try:
            stream = tts_plugin.synthesize(text)
            
            async for chunk in stream:
                frame = chunk.frame
                if audio_source is None:
                    # 첫 오디오 프레임에 맞춰 소스 생성
                    logger.info(f"🔊 AudioSource 초기화: {frame.sample_rate}Hz, {frame.num_channels}ch")
                    audio_source = rtc.AudioSource(frame.sample_rate, frame.num_channels)
                    audio_track = rtc.LocalAudioTrack.create_audio_track("agent-voice", audio_source)
                    await ctx.room.local_participant.publish_track(audio_track)

                await audio_source.capture_frame(frame)
                 
        except Exception as e:
            logger.error(f"TTS Error: {e}")

    @ctx.room.on("data_received")
    def on_data(data_packet, participant=None, kind=None, topic=None):
        try:
            # 1. payload 추출 (DataPacket 객체일 수도, bytes일 수도 있음)
            if hasattr(data_packet, 'data'):
                payload = data_packet.data
            else:
                payload = data_packet

            # 2. 바이트 디코딩
            if isinstance(payload, bytes):
                decoded_str = payload.decode('utf-8')
            else:
                decoded_str = str(payload)

            logger.info(f"📨 Raw Data Received: {decoded_str}")

            packet = Packet.from_json(decoded_str)

            
            # 1. 기억 저장
            memory.add_event(packet.event, packet.data)
            
            # 2. 반응 결정 (쿨다운 체크)
            if memory.should_alert(packet.event):
                asyncio.create_task(scold_user(packet))
            else:
                logger.info(f"🥶 쿨다운 중: {packet.event}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))