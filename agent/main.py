# agent/main.py
import asyncio
import logging
import sys, os
from dotenv import load_dotenv

load_dotenv()

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, tts, stt, vad
from livekit.plugins import elevenlabs, openai, silero

# shared 폴더 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.protocol import Packet
from shared.constants import SystemEvents
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

    # 3. STT & VAD 초기화
    stt_plugin = openai.STT()
    vad_plugin = silero.VAD.load()

    # 4. Audio Track 변수 (첫 오디오 데이터 수신 시 초기화)
    audio_source = None
    audio_track = None
    
    # 5. 현재 성격 (기본값)
    current_persona = "Strict Devil Instructor"

    async def handle_user_speech(track: rtc.Track):
        """사용자 오디오 트랙 처리 (STT -> LLM -> TTS)"""
        logger.info(f"🎤 Started listening to user track: {track.sid}")
        audio_stream = rtc.AudioStream(track)
        
        # STT 스트림 생성
        stt_stream = stt_plugin.stream()
        
        # VAD 스트림 생성 (음성 활동 감지용)
        vad_stream = vad_plugin.stream()

        async def _read_stt_results():
            nonlocal audio_source, audio_track, current_persona
            async for event in stt_stream:
                if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                    text = event.alternatives[0].text
                    if not text or len(text.strip()) < 2: continue
                    
                    logger.info(f"🗣️ User Said: {text}")
                    
                    # 🗣️ 사용자 핑계에 대한 LLM 처리
                    # SYSTEM_PROMPT의 {persona} 부분을 현재 성격으로 치환
                    formatted_system_prompt = SYSTEM_PROMPT.format(persona=current_persona)
                    
                    context_str = f"""
                    [NEW INTERACTION]
                    - User is talking back/making an excuse.
                    - User Said: "{text}"
                    
                    [Current Memory]
                    {memory.get_summary()}
                    
                    Determine if the user's excuse is valid. If not, scold them harder.
                    """
                    
                    try:
                        reply = await llm_handler.get_scolding(formatted_system_prompt, context_str)
                        logger.info(f"🤖 Reply to Excuse: {reply}")
                        
                        # TTS 송출 (scold_user 로직 재사용 가능하면 함수로 분리하는게 좋지만 일단 인라인)
                        stream = tts_plugin.synthesize(reply)
                        async for chunk in stream:
                            frame = chunk.frame
                            if audio_source is None:
                                logger.info(f"🔊 AudioSource 초기화 (Reply): {frame.sample_rate}Hz")
                                audio_source = rtc.AudioSource(frame.sample_rate, frame.num_channels)
                                audio_track = rtc.LocalAudioTrack.create_audio_track("agent-voice", audio_source)
                                await ctx.room.local_participant.publish_track(audio_track)
                            
                            await audio_source.capture_frame(frame)
                            
                    except Exception as e:
                        logger.error(f"Reply Error: {e}")

        # STT 결과 수신 태스크 시작
        asyncio.create_task(_read_stt_results())

        try:
            async for event in audio_stream:
                 # VAD 및 STT에 오디오 프레임 전달
                 stt_stream.push_frame(event.frame)
                 vad_stream.push_frame(event.frame)
        except Exception as e:
            logger.error(f"Audio Stream Error: {e}")
        finally:
            stt_stream.flush()
            stt_stream.end_input()

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(f"🎧 Subscribed to User Audio: {track.sid}")
            asyncio.create_task(handle_user_speech(track))

    async def scold_user(packet: Packet):
        nonlocal audio_source, audio_track, current_persona
        logger.info(f"⚡ 처형 프로세스 시작: {packet.event}")

        # A. 문맥 생성 (프롬프트에 페르소나 주입)
        # SYSTEM_PROMPT의 {persona} 부분을 현재 성격으로 치환
        formatted_system_prompt = SYSTEM_PROMPT.format(persona=current_persona)

        context_str = f"""
        [현재 상황]
        - 이벤트: {packet.event}
        - 상세: {packet.data}
        
        [기억 요약]
        {memory.get_summary()}
        """

        # B. LLM 멘트 생성
        try:
            text = await llm_handler.get_scolding(formatted_system_prompt, context_str)
            logger.info(f"🗣️ 생성된 잔소리 ({current_persona}): {text}")
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
        nonlocal current_persona # 외부 변수 수정을 위해 선언
        
        # 1. payload 추출 (DataPacket 객체일 수도, bytes일 수도 있음)
        try:
            if hasattr(data_packet, 'data'):
                payload = data_packet.data
            else:
                payload = data_packet

            # 2. 바이트 디코딩
            if isinstance(payload, bytes):
                decoded_str = payload.decode('utf-8')
            else:
                decoded_str = str(payload)
                
        except Exception as e:
            logger.error(f"❌ 데이터 디코딩 실패: {e}")
            return

        # 3. 패킷 파싱
        try:
            packet = Packet.from_json(decoded_str)
            logger.info(f"📨 Packet Received: {packet.event}") # 수신 로그 강화
        except Exception as e:
            logger.error(f"❌ JSON 파싱 실패: {e} / Raw: {decoded_str}")
            return

        try:
            # 0. 성격 변경 이벤트 처리
            if packet.event == SystemEvents.PERSONALITY_UPDATE:
                p_name = packet.data.get("personality", "Unknown")
                p_desc = packet.data.get("description", "")
                
                # 이름과 설명을 결합하여 LLM에게 풍부한 컨텍스트 제공
                if p_desc:
                    current_persona = f"{p_name}\n(Character Description: {p_desc})"
                else:
                    current_persona = p_name
                    
                logger.info(f"🎭 성격 변경됨: {current_persona}")
                return

            # 0.5 세션 시작 이벤트 (기억 초기화)
            if packet.event == SystemEvents.SESSION_START:
                logger.info("---------- 🆕 New Session Started: Memory Cleared ----------")
                memory.clear()
                return

            # 1. 반응 결정 (쿨다운 체크)
            if memory.should_alert(packet.event):
                # 2. 반응하기로 결정된 경우에만 기억 저장
                memory.add_event(packet.event, packet.data)
                
                # 3. 처형(잔소리) 시작
                asyncio.create_task(scold_user(packet))
            else:
                # 쿨다운 중이거나 무시할 이벤트
                pass
                
        except Exception as e:
            logger.error(f"❌ 로직 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))