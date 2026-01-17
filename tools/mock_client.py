import asyncio
import os
import sys
import json
import wave
from dotenv import load_dotenv
from livekit import rtc

# shared import (Packet 구조체 사용을 위해)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.protocol import Packet, PacketMeta

load_dotenv()

URL = os.getenv("LIVEKIT_URL")
TOKEN = os.getenv("LIVEKIT_TOKEN")

from livekit.api import AccessToken, VideoGrants

def get_token():
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("LIVEKIT_API_KEY and SECRET must be set")

    # can_subscribe=True가 기본값이지만 명시적으로 확인
    grant = VideoGrants(room_join=True, room="test-room", can_subscribe=True, can_publish=True)
    token = AccessToken(api_key, api_secret) \
        .with_grants(grant) \
        .with_identity("mock_user") \
        .with_name("MockUser")
    return token.to_jwt()

# 종료 이벤트를 위한 전역 변수
finished_event = asyncio.Event()

async def receive_audio(track: rtc.RemoteAudioTrack):
    print("🎧 Audio stream started saving to 'test_output.wav'")
    stream = rtc.AudioStream(track)
    
    with wave.open("test_output.wav", "wb") as wav_file:
        wav_file.setsampwidth(2) # 16-bit PCM
        wav_file.setnchannels(1) # default, will update
        wav_file.setframerate(24000) # default, will update
        
        first_frame = True
        iterator = stream.__aiter__()
        
        try:
            while True:
                # 첫 프레임은 오래 기다려주고(LLM 처리 시간), 그 뒤로는 3초 침묵하면 종료
                timeout = 15.0 if first_frame else 3.0
                
                try:
                    event = await asyncio.wait_for(iterator.__anext__(), timeout=timeout)
                    frame = event.frame

                    if first_frame:
                        print(f"📊 Format detected: {frame.sample_rate}Hz, {frame.num_channels}ch")
                        wav_file.setnchannels(frame.num_channels)
                        wav_file.setframerate(frame.sample_rate)
                        first_frame = False
                    
                    wav_file.writeframes(frame.data)
                
                except asyncio.TimeoutError:
                    if first_frame:
                        print("⚠️ Timeout: No audio received for 15s.")
                    else:
                        print("✅ Speech finished (Silence detected).")
                    break

        except Exception as e:
            print(f"⚠️ Audio receive error: {e}")
        finally:
            finished_event.set()

async def main():
    room = rtc.Room()
    
    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print(f"🔔 Track subscribed: {track.kind}")
            # 오디오 수신 태스크 시작
            asyncio.create_task(receive_audio(track))

    print(f"🔌 Connecting to {URL}...")
    try:
        await room.connect(URL, get_token())
        print("✅ Connected to room!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # 잠시 대기
    print("⏳ Waiting for connection stability...")
    await asyncio.sleep(2)

    # 가짜 데이터 생성
    packet = Packet(
        event="SLEEPING",
        data={"confidence": 0.99, "status": "deep_sleep"},
        meta=PacketMeta(category="VISION")
    )
    
    payload = packet.to_json().encode('utf-8')
    
    print(f"📤 Sending data: {packet.event}")
    
    await room.local_participant.publish_data(payload, reliable=True)
    print("✅ Data sent! waiting for audio...")
    
    # 종료 이벤트 대기 (오디오 수신이 끝나거나, 너무 오래 걸리면 종료)
    try:
        # 최대 30초 대기
        await asyncio.wait_for(finished_event.wait(), timeout=30.0)
    except asyncio.TimeoutError:
        print("⏰ Main Timeout: Test finished or no response.")
    finally:
        await room.disconnect()
        print("👋 Disconnected")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
