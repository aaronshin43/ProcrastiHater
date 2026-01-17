# client/services/vision.py
import sys
import os
from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import Image as MPImage
from mediapipe.tasks.python.vision.core.image import ImageFormat
import numpy as np
import time

# shared 폴더 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.protocol import Packet, PacketMeta
from shared.constants import VisionEvents, PacketCategory

class VisionWorker(QThread):
    # 메인 UI로 보낼 신호 정의
    alert_signal = pyqtSignal(object) # Packet 객체를 보냄

    def __init__(self, show_debug_window=False):
        super().__init__()
        self.running = False
        self.show_debug_window = show_debug_window  # 디버그 창 표시 여부
        # MediaPipe Face Landmarker 초기화 (0.10.x API)
        # 모델 파일 경로
        model_path = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"모델 파일을 찾을 수 없습니다: {model_path}\n"
                f"다음 명령으로 모델을 다운로드하세요: python download_mediapipe_model.py"
            )
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1,
            min_face_detection_confidence=0.3,  # 부분 얼굴도 감지하도록 낮춤
            min_face_presence_confidence=0.3,   # 부분 얼굴도 감지하도록 낮춤
            min_tracking_confidence=0.3,        # tracking 유지
            running_mode=vision.RunningMode.IMAGE  # 이미지 모드
        )
        
        try:
            self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
        except Exception as e:
            print(f"⚠️ FaceLandmarker 초기화 실패: {e}")
            print("💡 모델 파일을 다운로드하거나 다른 방법을 시도해주세요.")
            raise
        
        # 상태 추적 (카운터 방식)
        self.eye_closed_counter = 0  # 눈 감음 연속 프레임 카운터
        self.no_face_counter = 0  # 얼굴 부재 연속 프레임 카운터
        self.gaze_away_counter = 0  # 시선 벗어남 연속 프레임 카운터 (얼굴 있음 + 눈 없음)
        self.last_alert_time = {}  # 각 이벤트별 마지막 알림 시간 (중복 방지)
        
        # Tracking fallback (얼굴이 잠깐 안 보여도 유지)
        self.last_face_landmarks = None  # 이전 프레임의 얼굴 랜드마크
        self.last_face_detection_time = 0  # 마지막 얼굴 감지 시간
        self.face_tracking_timeout = 0.5  # 얼굴이 감지되지 않아도 0.5초간 tracking 유지
        
        # EAR 임계값
        self.EAR_THRESHOLD = 0.25  # 눈 감음 임계값
        self.EAR_CONSECUTIVE_FRAMES = 100  # 연속 프레임 수 (졸음 감지 임계값)
        self.NO_FACE_CONSECUTIVE_FRAMES = 100  # 얼굴 부재 연속 프레임 수
        
        # GAZE_AWAY: 얼굴 있음 + 눈 없음이 지속되는 프레임 수
        self.GAZE_AWAY_CONSECUTIVE_FRAMES = 10  # 연속 프레임 수 (약 5초)
        
        # 얼굴 외곽선 랜드마크 (그리기용)
        self.FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        
        # 얼굴 방향 계산용 추가 랜드마크
        self.LEFT_EYE_INNER = 133
        self.LEFT_EYE_OUTER = 33
        self.RIGHT_EYE_INNER = 362
        self.RIGHT_EYE_OUTER = 263
        self.FOREHEAD = 10
        
        # 눈 랜드마크 인덱스 (EAR 계산용)
        self.LEFT_EYE_EAR = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_EAR = [362, 385, 387, 263, 390, 374]
        
        # 얼굴 방향 계산용 랜드마크
        self.NOSE_TIP = 1
        self.CHIN = 175
        self.LEFT_EYE_CENTER = 33
        self.RIGHT_EYE_CENTER = 362
    
    def calculate_ear(self, landmarks, eye_indices):
        """Eye Aspect Ratio (EAR) 계산"""
        # MediaPipe 0.10.x는 landmarks가 리스트 형태
        # 수직 거리 계산
        vertical_1 = np.linalg.norm(
            np.array([landmarks[eye_indices[1]].x, landmarks[eye_indices[1]].y]) -
            np.array([landmarks[eye_indices[5]].x, landmarks[eye_indices[5]].y])
        )
        vertical_2 = np.linalg.norm(
            np.array([landmarks[eye_indices[2]].x, landmarks[eye_indices[2]].y]) -
            np.array([landmarks[eye_indices[4]].x, landmarks[eye_indices[4]].y])
        )
        
        # 수평 거리 계산
        horizontal = np.linalg.norm(
            np.array([landmarks[eye_indices[0]].x, landmarks[eye_indices[0]].y]) -
            np.array([landmarks[eye_indices[3]].x, landmarks[eye_indices[3]].y])
        )
        
        # EAR 계산
        if horizontal == 0:
            return 0.0
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear
    
    def should_alert(self, event_type, cooldown_seconds=5):
        """중복 알림 방지 (쿨다운)"""
        current_time = time.time()
        last_time = self.last_alert_time.get(event_type, 0)
        
        if current_time - last_time < cooldown_seconds:
            return False
        
        self.last_alert_time[event_type] = current_time
        return True
    
    def has_eyes_visible(self, face_landmarks):
        """눈 랜드마크가 보이는지 확인 (얼굴이 옆으로 돌아가면 눈이 가려질 수 있음)"""
        try:
            # 왼쪽 눈과 오른쪽 눈의 주요 랜드마크 확인
            left_eye_valid = all(i < len(face_landmarks) for i in self.LEFT_EYE_EAR)
            right_eye_valid = all(i < len(face_landmarks) for i in self.RIGHT_EYE_EAR)
            
            # 양쪽 눈 중 하나라도 랜드마크가 유효하면 눈이 보이는 것으로 판단
            return left_eye_valid or right_eye_valid
        except (IndexError, AttributeError):
            return False
    
    def calculate_face_orientation(self, landmarks, frame_width, frame_height):
        """얼굴 방향 계산 (pitch, yaw) - 기하학적 계산 기반"""
        # 주요 얼굴 랜드마크 추출
        nose_tip = landmarks[self.NOSE_TIP]
        chin = landmarks[self.CHIN]
        left_eye_inner = landmarks[self.LEFT_EYE_INNER]
        left_eye_outer = landmarks[self.LEFT_EYE_OUTER]
        right_eye_inner = landmarks[self.RIGHT_EYE_INNER]
        right_eye_outer = landmarks[self.RIGHT_EYE_OUTER]
        forehead = landmarks[self.FOREHEAD]
        
        # 2D 좌표 추출 (x, y만 사용 - 더 안정적)
        def get_2d(landmark):
            return np.array([landmark.x, landmark.y])
        
        nose_2d = get_2d(nose_tip)
        chin_2d = get_2d(chin)
        left_eye_inner_2d = get_2d(left_eye_inner)
        left_eye_outer_2d = get_2d(left_eye_outer)
        right_eye_inner_2d = get_2d(right_eye_inner)
        right_eye_outer_2d = get_2d(right_eye_outer)
        forehead_2d = get_2d(forehead)
        
        # 두 눈의 중심점 계산
        left_eye_center_2d = (left_eye_inner_2d + left_eye_outer_2d) / 2
        right_eye_center_2d = (right_eye_inner_2d + right_eye_outer_2d) / 2
        eye_center_2d = (left_eye_center_2d + right_eye_center_2d) / 2
        
        # 두 눈 사이의 거리 (정규화된 좌표 기준)
        eye_distance = np.linalg.norm(right_eye_center_2d - left_eye_center_2d)
        
        # 얼굴 높이 (이마에서 턱까지)
        face_height = np.linalg.norm(chin_2d - forehead_2d)
        
        # Yaw 계산 (좌우 회전) - 코가 두 눈 중심선에서 얼마나 벗어났는지
        # 정면을 보면 코는 두 눈 중심선의 중앙에 있어야 함
        eye_midpoint_x = eye_center_2d[0]
        nose_x = nose_2d[0]
        
        # 코가 눈 중심선에서 벗어난 거리 (정규화)
        if eye_distance > 0:
            yaw_offset = (nose_x - eye_midpoint_x) / eye_distance
            # 각도로 변환 (대략적인 변환: 정면 기준 ±30도 범위)
            # yaw_offset이 0이면 정면, ±0.5면 약 30도 회전
            yaw_degrees = yaw_offset * 60.0  # 스케일 조정
        else:
            yaw_degrees = 0.0
        
        # Pitch 계산 (상하 회전) - 코가 눈 중심선에서 얼마나 위아래로 벗어났는지
        # 정면을 보면 코는 눈 중심선보다 약간 아래에 있어야 함
        eye_midpoint_y = eye_center_2d[1]
        nose_y = nose_2d[1]
        
        # 코가 눈 중심선보다 아래에 있으면 양수 (아래로 고개를 숙임)
        # 코가 눈 중심선보다 위에 있으면 음수 (위로 고개를 듦)
        if face_height > 0:
            # 정면 기준으로 코는 눈보다 약간 아래에 있어야 함
            # 정상적인 위치 차이를 보정
            normal_nose_offset = 0.05  # 정면 기준 코의 정상 위치 (눈보다 약간 아래)
            pitch_offset = (nose_y - eye_midpoint_y - normal_nose_offset) / face_height
            # 각도로 변환
            pitch_degrees = pitch_offset * 60.0  # 스케일 조정
        else:
            pitch_degrees = 0.0
        
        return pitch_degrees, yaw_degrees
    
    def draw_debug_info(self, frame, face_landmarks, avg_ear, pitch, yaw, is_sleeping, is_absent, is_gaze_away):
        """디버그 정보를 프레임에 그리기"""
        frame_height, frame_width = frame.shape[:2]
        
        # 상태 정보 텍스트
        y_offset = 30
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        # 얼굴 감지 여부 표시
        if face_landmarks:
            # 얼굴이 감지됨
            cv2.putText(frame, "Face: DETECTED", (10, y_offset),
                       font, font_scale, (0, 255, 0), thickness)
            
            # 얼굴 외곽선 그리기 (얼굴 감지 표시)
            face_oval_points = []
            for idx in self.FACE_OVAL:
                if idx < len(face_landmarks):
                    point = face_landmarks[idx]
                    x = int(point.x * frame_width)
                    y = int(point.y * frame_height)
                    face_oval_points.append((x, y))
            
            if len(face_oval_points) > 2:
                pts = np.array(face_oval_points, np.int32)
                cv2.polylines(frame, [pts], True, (255, 0, 255), 2)  # 마젠타색으로 얼굴 외곽선
            
            # 눈 가시성 확인
            eyes_visible = self.has_eyes_visible(face_landmarks)
            
            # 눈 영역 그리기 (눈이 보일 때만)
            if eyes_visible:
                for eye_indices in [self.LEFT_EYE_EAR, self.RIGHT_EYE_EAR]:
                    eye_points = []
                    for idx in eye_indices:
                        if idx < len(face_landmarks):
                            point = face_landmarks[idx]
                            x = int(point.x * frame_width)
                            y = int(point.y * frame_height)
                            eye_points.append((x, y))
                            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
                    
                    # 눈 윤곽선 그리기
                    if len(eye_points) >= 4:
                        pts = np.array(eye_points, np.int32)
                        cv2.polylines(frame, [pts], True, (0, 255, 0), 1)
            else:
                # 눈이 안 보이는 경우 표시
                cv2.putText(frame, "Eyes: NOT VISIBLE", (10, y_offset + 25),
                           font, font_scale, (0, 165, 255), thickness)
            
            y_offset += 25
            
            # 눈 가시성 표시
            eyes_status = "VISIBLE" if eyes_visible else "NOT VISIBLE"
            eyes_color = (0, 255, 0) if eyes_visible else (0, 165, 255)
            cv2.putText(frame, f"Eyes: {eyes_status}", (10, y_offset),
                       font, font_scale, eyes_color, thickness)
            y_offset += 25
            
            # EAR 값 (눈이 보일 때만 표시)
            if eyes_visible and avg_ear > 0:
                ear_color = (0, 255, 0) if avg_ear >= self.EAR_THRESHOLD else (0, 0, 255)
                cv2.putText(frame, f"EAR: {avg_ear:.3f}", (10, y_offset), 
                           font, font_scale, ear_color, thickness)
                y_offset += 25
            
            # 시선 벗어남 프레임 수
            gaze_away_color = (255, 255, 255) if not is_gaze_away else (0, 165, 255)
            cv2.putText(frame, f"Gaze Away Frames: {self.gaze_away_counter}/{self.GAZE_AWAY_CONSECUTIVE_FRAMES}", 
                       (10, y_offset), font, font_scale, gaze_away_color, thickness)
            y_offset += 25
            
            # 눈 감음 프레임 수
            cv2.putText(frame, f"Closed Frames: {self.eye_closed_counter}/{self.EAR_CONSECUTIVE_FRAMES}", 
                       (10, y_offset), font, font_scale, (255, 255, 255), thickness)
            y_offset += 25
        else:
            # 얼굴이 감지되지 않음
            cv2.putText(frame, "Face: NOT DETECTED", (10, y_offset),
                       font, font_scale, (0, 0, 255), thickness)
            y_offset += 25
            
            # 얼굴 부재 프레임 수
            cv2.putText(frame, f"No Face Frames: {self.no_face_counter}/{self.NO_FACE_CONSECUTIVE_FRAMES}", 
                       (10, y_offset), font, font_scale, (255, 255, 255), thickness)
            y_offset += 25
        
        # 상태 표시 (항상 표시)
        if is_sleeping:
            cv2.putText(frame, "SLEEPING!", (10, y_offset),
                       font, 0.8, (0, 0, 255), 2)
            y_offset += 30
        if is_absent:
            cv2.putText(frame, "ABSENT!", (10, y_offset),
                       font, 0.8, (255, 0, 0), 2)
            y_offset += 30
        if is_gaze_away:
            cv2.putText(frame, "GAZE AWAY!", (10, y_offset),
                       font, 0.8, (0, 165, 255), 2)
            y_offset += 30
        
        return frame

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] 웹캠을 열 수 없습니다. 웹캠이 연결되어 있는지 확인하세요.")
            self.running = False
            return
        
        print("[OK] 웹캠 연결 성공 - Vision Worker 시작")
        
        try:
            while self.running:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        print("[WARNING] 프레임을 읽을 수 없습니다")
                        continue
                    
                    # MediaPipe Face Landmarker 처리
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = MPImage(image_format=ImageFormat.SRGB, data=frame_rgb)
                    detection_result = self.face_landmarker.detect(mp_image)
                    
                    is_sleeping = False
                    is_absent = False
                    is_gaze_away = False
                    avg_ear = 0.0  # 기본값
                    pitch, yaw = 0.0, 0.0  # 얼굴 방향 (각도, 도 단위)
                    
                    current_time = time.time()
                    face_detected = False
                    face_landmarks = None
                    
                    # 1단계: 얼굴 감지 확인
                    if detection_result.face_landmarks and len(detection_result.face_landmarks) > 0:
                        face_landmarks = detection_result.face_landmarks[0]
                        self.last_face_landmarks = face_landmarks
                        self.last_face_detection_time = current_time
                        face_detected = True
                        self.no_face_counter = 0  # 얼굴 감지되면 카운터 리셋
                    
                    # 2단계: Tracking fallback (짧은 시간만)
                    elif self.last_face_landmarks is not None:
                        time_since_last = current_time - self.last_face_detection_time
                        if time_since_last < self.face_tracking_timeout:
                            face_landmarks = self.last_face_landmarks
                            face_detected = True
                        else:
                            # Tracking timeout - 얼굴이 완전히 사라진 것으로 간주
                            self.last_face_landmarks = None
                            self.no_face_counter += 1
                            self.eye_closed_counter = 0
                            self.gaze_away_counter = 0
                    else:
                        # 얼굴이 감지되지 않고 이전 정보도 없음
                        self.no_face_counter += 1
                        self.eye_closed_counter = 0
                        self.gaze_away_counter = 0
                    
                    # 3단계: 얼굴이 감지되었거나 tracking 중인 경우
                    if face_detected and face_landmarks is not None:
                        # 눈 가시성 확인
                        eyes_visible = self.has_eyes_visible(face_landmarks)
                        
                        if eyes_visible:
                            # 얼굴 + 눈이 보임 - 정상 상태
                            self.gaze_away_counter = 0  # GAZE_AWAY 카운터 리셋
                            
                            # 눈 감음 감지 (EAR 계산)
                            try:
                                left_ear = self.calculate_ear(face_landmarks, self.LEFT_EYE_EAR)
                            except (IndexError, AttributeError):
                                left_ear = 0.0
                            
                            try:
                                right_ear = self.calculate_ear(face_landmarks, self.RIGHT_EYE_EAR)
                            except (IndexError, AttributeError):
                                right_ear = 0.0
                            
                            if left_ear > 0 and right_ear > 0:
                                avg_ear = (left_ear + right_ear) / 2.0
                            elif left_ear > 0:
                                avg_ear = left_ear
                            elif right_ear > 0:
                                avg_ear = right_ear
                            
                            # 눈이 감겼는지 확인
                            if avg_ear > 0:
                                if avg_ear < self.EAR_THRESHOLD:
                                    # 눈이 감음 - 카운터 증가
                                    self.eye_closed_counter += 1
                                else:
                                    # 눈이 열림 - 카운터 리셋
                                    self.eye_closed_counter = 0
                                
                                # 연속으로 눈을 감고 있으면 졸음 감지
                                if self.eye_closed_counter >= self.EAR_CONSECUTIVE_FRAMES:
                                    is_sleeping = True
                        else:
                            # 얼굴은 보이지만 눈이 안 보임 - GAZE_AWAY 상태
                            self.eye_closed_counter = 0  # 눈 감음 카운터는 리셋
                            self.gaze_away_counter += 1  # GAZE_AWAY 카운터 증가
                            
                            # 연속으로 얼굴은 보이지만 눈이 안 보이면 GAZE_AWAY 감지
                            if self.gaze_away_counter >= self.GAZE_AWAY_CONSECUTIVE_FRAMES:
                                is_gaze_away = True
                    
                    # 4단계: 얼굴이 완전히 사라진 경우
                    if not face_detected and self.last_face_landmarks is None:
                        if self.no_face_counter >= self.NO_FACE_CONSECUTIVE_FRAMES:
                            is_absent = True
                    
                    # 졸음 감지 시 Packet 발송
                    if is_sleeping:
                        if self.should_alert(VisionEvents.SLEEPING):
                            packet = Packet(
                                event=VisionEvents.SLEEPING,
                                data={"confidence": 0.9, "ear": avg_ear},
                                meta=PacketMeta(category=PacketCategory.VISION)
                            )
                            self.alert_signal.emit(packet)
                    
                    # 얼굴 부재 감지 시 Packet 발송
                    if is_absent:
                        if self.should_alert(VisionEvents.ABSENT):
                            packet = Packet(
                                event=VisionEvents.ABSENT,
                                data={"confidence": 0.9, "duration": self.no_face_counter},
                                meta=PacketMeta(category=PacketCategory.VISION)
                            )
                            self.alert_signal.emit(packet)
                    
                    # 시선 벗어남 감지 시 Packet 발송 (얼굴 있음 + 눈 없음)
                    if is_gaze_away:
                        if self.should_alert(VisionEvents.GAZE_AWAY):
                            packet = Packet(
                                event=VisionEvents.GAZE_AWAY,
                                data={
                                    "confidence": 0.9, 
                                    "reason": "eyes_not_visible",
                                    "duration": self.gaze_away_counter
                                },
                                meta=PacketMeta(category=PacketCategory.VISION)
                            )
                            self.alert_signal.emit(packet)
                    
                    # 디버그 창 표시 (얼굴이 있든 없든 항상 표시)
                    if self.show_debug_window:
                        # 얼굴 랜드마크 추출
                        face_landmarks_for_draw = None
                        if detection_result.face_landmarks:
                            face_landmarks_for_draw = detection_result.face_landmarks[0]
                        
                        debug_frame = self.draw_debug_info(
                            frame.copy(), 
                            face_landmarks_for_draw,
                            avg_ear, pitch, yaw, is_sleeping, is_absent, is_gaze_away
                        )
                        cv2.imshow('Vision Debug', debug_frame)
                        # 'q' 키를 누르면 종료
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            self.running = False
                    
                    # time.sleep(0.05) # 0.1초 대기 (10 FPS)
                
                except Exception as e:
                    # 프레임 처리 중 예외 발생 시 로그 출력하고 계속 진행
                    print(f"[ERROR] 프레임 처리 중 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
                    # 예외 발생해도 루프는 계속 진행 (다음 프레임 처리)
                    continue
        
        except Exception as e:
            # 전체 루프에서 치명적 오류 발생 시
            print(f"[ERROR] Vision Worker 치명적 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 정리 작업은 항상 실행
            self.running = False
            cap.release()
            if self.show_debug_window:
                cv2.destroyAllWindows()
            print("[OK] Vision Worker 종료")
    
    def stop(self):
        """스레드 종료"""
        self.running = False