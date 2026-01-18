import threading
import queue
import sounddevice as sd
import numpy as np
import asyncio
from livekit import rtc

class AudioSink(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.daemon = True
        self.stream = None
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            try:
                # 큐에서 오디오 프레임 데이터 가져오기 (타임아웃 설정으로 종료 체크)
                frame_info = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue

            data, sample_rate, channels = frame_info

            # 스트림 초기화 또는 포맷 변경 시 재초기화
            if self.stream is None or self.stream.samplerate != sample_rate or self.stream.channels != channels:
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
                
                try:
                    self.stream = sd.OutputStream(
                        samplerate=sample_rate,
                        channels=channels,
                        dtype='int16'
                    )
                    self.stream.start()
                    print(f"🔊 Audio Sink Initialized: {sample_rate}Hz, {channels}ch")
                except Exception as e:
                    print(f"❌ Failed to initialize audio stream: {e}")
                    continue

            # 오디오 재생 (Blocking Write)
            try:
                self.stream.write(data)
            except Exception as e:
                print(f"❌ Audio Write Error: {e}")

    def put_frame(self, frame: rtc.AudioFrame):
        # AudioFrame을 numpy로 변환 및 정보 추출
        # frame.data는 int16 memoryview
        data = np.frombuffer(frame.data, dtype=np.int16)
        # livekit 0.17+ AudioFrame uses num_channels instead of channels
        self.queue.put((data, frame.sample_rate, frame.num_channels))
    
    def clear(self):
        """큐를 비워 재생을 즉시 중단하는 효과"""
        with self.queue.mutex:
            self.queue.queue.clear()
        
        # 스트림도 플러시 (가능하다면) - sounddevice는 abort가 있긴 함
        if self.stream and self.stream.active:
             self.stream.abort()
             self.stream.close()
             self.stream = None

    def stop(self):
        self._stop_event.set()
        if self.stream:
            self.stream.stop()
            self.stream.close()

class AudioPlayer:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.sink = AudioSink()
        self.sink.start()
        self.task = None
        self._is_muted = False  # Track interruption state

    def set_muted(self, muted: bool):
        self._is_muted = muted
        if muted:
            self.sink.clear()

    async def start(self, track: rtc.Track):
        self.task = self.loop.create_task(self._consume_track(track))

    async def _consume_track(self, track: rtc.Track):
        audio_stream = rtc.AudioStream(track)
        print(f"🎧 Started listening to track: {track.sid}")
        try:
            async for event in audio_stream:
                if self._is_muted:
                    continue  # Muted 상태면 재생 큐에 넣지 않고 버림
                
                # LiveKit 0.17.x 이상에서는 AudioStream이 AudioFrameEvent를 반환합니다.
                # 실제 오디오 데이터는 event.frame에 들어있습니다.
                self.sink.put_frame(event.frame)
        except Exception as e:
            print(f"❌ Audio consumption logic error: {e}")
        finally:
            print(f"🔇 Stopped listening to track: {track.sid}")

    def stop(self):
        if self.task:
            self.task.cancel()
        self.sink.stop()
        
    async def stop_async(self):
        """Helper for async context"""
        self.sink.clear()

    async def stop_async(self):
        """인터럽트용: 즉시 재생을 멈추고 큐를 비움"""
        self.sink.clear()
        print("🔇 Audio Player Interrupted (Cleared Buffer)")
