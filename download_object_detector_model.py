"""
MediaPipe Object Detector 모델 다운로드 스크립트
EfficientDet-Lite0 모델 (COCO 데이터셋 기반, cell phone 클래스 포함)
"""
import os
import urllib.request

# MediaPipe Object Detector 모델 URL (EfficientDet-Lite0)
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/float16/1/efficientdet_lite0.tflite"
MODEL_PATH = os.path.join("client", "services", "efficientdet_lite0.tflite")

def download_model():
    """Object Detector 모델 다운로드"""
    print(f"다운로드 중: {MODEL_URL}")
    print(f"저장 위치: {MODEL_PATH}")
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"[OK] 모델 다운로드 완료: {MODEL_PATH}")
        print(f"파일 크기: {os.path.getsize(MODEL_PATH) / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"[ERROR] 다운로드 실패: {e}")
        print(f"[INFO] 모델 URL이 변경되었을 수 있습니다. MediaPipe 공식 문서를 확인하세요.")
        return False
    
    return True

if __name__ == "__main__":
    download_model()
