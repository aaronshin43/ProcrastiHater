# client/services/screen.py
"""
Screen Monitoring Service - Windows 활성 창 제목 모니터링

[주요 기능]
1. 활성 창 제목 추출
   - 현재 포커스된 창의 제목을 실시간으로 감지
   - 크롬, VS Code 등 모든 애플리케이션 창 제목 추출
   - 창 전환 시 WINDOW_CHANGE 이벤트 발송

[이벤트 타입]
- WINDOW_CHANGE: 활성 창이 변경되었을 때

[사용 예시]
    screen_worker = ScreenWorker()
    screen_worker.alert_signal.connect(on_alert)
    screen_worker.start()
"""

import sys
import os
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal

# Windows API (pywin32)
try:
    import win32gui
    import win32process
    import win32con
    import psutil
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("[WARNING] Windows API를 사용할 수 없습니다. pywin32와 psutil이 설치되어 있는지 확인하세요.")

# ctypes for SetWinEventHook (not available in win32gui)
if WINDOWS_AVAILABLE:
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        ole32 = ctypes.windll.ole32
        
        # SetWinEventHook 함수 타입 정의
        WINEVENTPROC = ctypes.WINFUNCTYPE(
            None,
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.HWND,
            ctypes.c_long,
            ctypes.c_long,
            wintypes.DWORD,
            wintypes.DWORD
        )
        
        EVENT_HOOK_AVAILABLE = True
    except Exception as e:
        EVENT_HOOK_AVAILABLE = False
        print(f"[WARNING] Event Hook 기능을 사용할 수 없습니다: {e}")
else:
    EVENT_HOOK_AVAILABLE = False

# shared 폴더 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.protocol import Packet, PacketMeta
from shared.constants import ScreenEvents, PacketCategory

class ScreenWorker(QThread):
    """Windows 활성 창 제목 모니터링"""
    # 메인 UI로 보낼 신호 정의
    alert_signal = pyqtSignal(object)  # Packet 객체를 보냄
    
    def __init__(self, check_interval=2.0):
        super().__init__()
        self.running = False
        
        # 창 제목 체크 간격
        self.window_check_interval = 0.05  # 창 제목 체크 간격 (50ms) - 크롬 탭 변경 감지용
        self._last_window_title_check = 0  # 마지막 창 제목 체크 시간
        
        # 이벤트 기반 창 감지 (사용 안 함으로 설정 - 폴링 모드 사용)
        self.use_event_hook = False  # 이벤트 기반 창 감지 사용 여부
        self._event_hook_handle = None  # Windows Event Hook 핸들
        self._win_event_callback = None  # 콜백 함수 참조 유지 (가비지 컬렉션 방지)
        
        self.last_alert_time = {}  # 각 이벤트별 마지막 알림 시간 (중복 방지)
        
        # 스레드 동기화를 위한 Lock (경쟁 조건 방지)
        self._check_lock = threading.Lock()
        
        # 현재 상태 추적
        self.current_window_title = None
        self.current_process_name = None
        
        if not WINDOWS_AVAILABLE:
            print("[WARNING] Screen Worker가 Windows 환경에서만 작동합니다.")
    
    def get_active_window_title(self):
        """현재 활성 창의 제목 가져오기"""
        if not WINDOWS_AVAILABLE:
            return None
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            return window_title if window_title else None
        except Exception as e:
            print(f"[WARNING] 활성 창 제목 가져오기 실패: {e}")
            return None
    
    def get_active_process_name(self):
        """현재 활성 창의 프로세스 이름 가져오기"""
        if not WINDOWS_AVAILABLE:
            return None
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name().lower()
        except Exception as e:
            print(f"[WARNING] 활성 프로세스 이름 가져오기 실패: {e}")
            return None
    
    def _check_window_title_change(self):
        """
        창 제목 변경 체크 (크롬 탭 변경 등 감지용)
        마우스로 클릭할 때 앱이 detect 되는 기능
        
        Thread-safe: 여러 스레드에서 동시 호출되어도 경쟁 조건 방지
        """
        # Lock을 사용하여 동시 실행 방지 (경쟁 조건 방지)
        with self._check_lock:
            try:
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd:
                    window_title = win32gui.GetWindowText(current_hwnd)
                    if window_title and window_title != self.current_window_title:
                        self.current_window_title = window_title
                        
                        # 창 변경 시에만 프로세스 이름 가져오기
                        process_name = self.get_active_process_name()
                        self.current_process_name = process_name
                        
                        # WINDOW_CHANGE 이벤트 발송
                        if self.should_alert(ScreenEvents.WINDOW_CHANGE):
                            packet = Packet(
                                event=ScreenEvents.WINDOW_CHANGE,
                                data={
                                    "window_title": window_title,
                                    "process_name": process_name or "unknown"
                                },
                                meta=PacketMeta(category=PacketCategory.SCREEN)
                            )
                            self.alert_signal.emit(packet)
                            print(f"[SCREEN] 창 변경: {window_title}")
                        
                        return True
                return False
            except Exception as e:
                print(f"[WARNING] 창 제목 확인 중 오류: {e}")
                return False
    
    def _on_window_focus_change(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsTimeStamp):
        """
        Windows Event Hook 콜백: 창 포커스 변경 시 즉시 호출됨
        이벤트 기반으로 즉시 반응 (CPU 사용량 거의 0, 딜레이 없음)
        크롬 탭 변경도 즉시 감지
        """
        try:
            # 활성 창이 변경되었을 때만 처리
            if event == win32con.EVENT_SYSTEM_FOREGROUND:
                # 약간의 지연 후 창 제목 가져오기 (크롬 탭 변경 시 제목 업데이트 대기)
                def check_window_title():
                    time.sleep(0.05)  # 50ms 대기 (크롬이 제목 업데이트할 시간)
                    if not self.running:
                        return
                    
                    # 창 제목 변경 체크
                    self._check_window_title_change()
                
                # 별도 스레드에서 실행 (메인 루프 블로킹 방지)
                threading.Thread(target=check_window_title, daemon=True).start()
        except Exception as e:
            print(f"[WARNING] 창 포커스 변경 콜백 오류: {e}")
    
    def should_alert(self, event_type, cooldown_seconds=5):
        """
        중복 알림 방지 (쿨다운)
        
        WINDOW_CHANGE 이벤트는 쿨다운 없이 즉시 발송 (크롬 탭 변경 등 빠른 반응 필요)
        """
        # WINDOW_CHANGE는 쿨다운 없이 항상 발송 (크롬 탭 변경 등 즉시 반응 필요)
        if event_type == ScreenEvents.WINDOW_CHANGE:
            return True
        
        current_time = time.time()
        last_time = self.last_alert_time.get(event_type, 0)
        
        if current_time - last_time < cooldown_seconds:
            return False
        
        self.last_alert_time[event_type] = current_time
        return True
    
    def run(self):
        """
        메인 모니터링 루프 (창 제목 변경 감지)
        마우스로 클릭할 때 앱이 detect 되는 기능
        """
        if not WINDOWS_AVAILABLE:
            print("[ERROR] Screen Worker는 Windows 환경에서만 작동합니다.")
            return
        
        self.running = True
        print("[OK] Screen Worker 시작 - 활성 창 제목 모니터링")
        
        # ========== Windows Event Hook 설정 (이벤트 기반 창 감지) ==========
        if self.use_event_hook and WINDOWS_AVAILABLE and EVENT_HOOK_AVAILABLE:
            try:
                # Windows Event Hook 설정
                # EVENT_SYSTEM_FOREGROUND: 활성 창이 변경될 때 발생
                # Bug Fix 1: 콜백 함수를 인스턴스 변수로 저장하여 가비지 컬렉션 방지
                def win_event_callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsTimeStamp):
                    """Windows Event Hook 콜백 래퍼"""
                    if self.running:
                        self._on_window_focus_change(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsTimeStamp)
                
                # 콜백 함수 참조 유지 (가비지 컬렉션 방지)
                self._win_event_callback = WINEVENTPROC(win_event_callback)
                
                # Bug Fix 2: ctypes를 사용하여 SetWinEventHook 직접 호출
                # win32gui에는 SetWinEventHook이 없으므로 ctypes로 직접 바인딩
                SetWinEventHook = user32.SetWinEventHook
                SetWinEventHook.argtypes = [
                    wintypes.DWORD,  # eventMin
                    wintypes.DWORD,  # eventMax
                    wintypes.HMODULE,  # hmodWinEventProc
                    WINEVENTPROC,  # lpfnWinEventProc
                    wintypes.DWORD,  # idProcess
                    wintypes.DWORD,  # idThread
                    wintypes.DWORD   # dwFlags
                ]
                SetWinEventHook.restype = wintypes.HANDLE
                
                # Event Hook 등록
                self._event_hook_handle = SetWinEventHook(
                    win32con.EVENT_SYSTEM_FOREGROUND,  # 이벤트 타입: 활성 창 변경
                    win32con.EVENT_SYSTEM_FOREGROUND,  # 이벤트 범위
                    0,  # hmodWinEventProc (0 = 현재 프로세스)
                    self._win_event_callback,  # 콜백 함수
                    0,  # 프로세스 ID (0 = 모든 프로세스)
                    0,  # 스레드 ID (0 = 모든 스레드)
                    win32con.WINEVENT_OUTOFCONTEXT  # 컨텍스트
                )
                
                if self._event_hook_handle:
                    print("[INFO] 이벤트 기반 창 감지 활성화 (즉시 반응, CPU 사용량 거의 0)")
                else:
                    raise Exception("SetWinEventHook returned NULL")
            except Exception as e:
                print(f"[WARNING] 이벤트 기반 창 감지 설정 실패, 폴링 모드로 전환: {e}")
                import traceback
                traceback.print_exc()
                self.use_event_hook = False
                self._win_event_callback = None
        
        try:
            while self.running:
                try:
                    current_time = time.time()
                    
                    # ========== 창 제목 체크 (크롬 탭 변경 감지용) ==========
                    # 이벤트 기반으로는 창 포커스 변경만 감지되므로,
                    # 크롬 탭 변경 등 제목만 바뀌는 경우를 위해 주기적으로 체크
                    if current_time - self._last_window_title_check >= self.window_check_interval:
                        self._check_window_title_change()
                        self._last_window_title_check = current_time
                    
                    # 이벤트 기반 모드: Windows 메시지 펌프 (이벤트 처리)
                    if self.use_event_hook:
                        # Windows 메시지 펌프를 통해 이벤트 처리
                        win32gui.PumpWaitingMessages()
                        time.sleep(0.05)  # 매우 짧은 대기 (크롬 탭 변경 감지 반응성 향상)
                    else:
                        # 폴링 모드 (이벤트 훅이 실패한 경우)
                        time.sleep(0.05)  # 창 제목 체크 간격과 동일하게 설정
                
                except Exception as e:
                    print(f"[ERROR] Screen Worker 프레임 처리 중 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(0.1)
                    continue
        
        except Exception as e:
            print(f"[ERROR] Screen Worker 치명적 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            
            # Event Hook 해제
            if self._event_hook_handle:
                try:
                    # Bug Fix 2: ctypes를 사용하여 UnhookWinEventHook 직접 호출
                    if EVENT_HOOK_AVAILABLE:
                        UnhookWinEventHook = user32.UnhookWinEvent
                        UnhookWinEventHook.argtypes = [wintypes.HANDLE]
                        UnhookWinEventHook.restype = wintypes.BOOL
                        UnhookWinEventHook(self._event_hook_handle)
                    self._event_hook_handle = None
                    self._win_event_callback = None  # 콜백 참조 해제
                    print("[INFO] Event Hook 해제 완료")
                except Exception as e:
                    print(f"[WARNING] Event Hook 해제 실패: {e}")
            
            print("[OK] Screen Worker 종료")
    
    def stop(self):
        """스레드 종료"""
        self.running = False
