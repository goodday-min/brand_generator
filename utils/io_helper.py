"""
JSON 로드/저장, 이미지 다운로드, 폴더 생성 등 파일 관련 유틸리티
"""
import json
import base64
from pathlib import Path
import requests


def load_json(path: Path) -> dict:
    """JSON 파일을 읽어서 딕셔너리로 돌려줍니다."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    """딕셔너리를 JSON 파일로 저장합니다 (한글 유지, 들여쓰기 2칸)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_dir(path: Path) -> Path:
    """폴더가 없으면 만들어줍니다 (중간 폴더도 자동 생성)."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_image(image_data: str, save_path: Path, timeout: int = 30) -> Path:
    """
    이미지 데이터를 파일로 저장합니다.
    URL(dall-e-3 스타일)과 Base64(gpt-image-1 스타일) 모두 지원합니다.

    Args:
        image_data: 이미지 URL 또는 Base64 인코딩된 문자열
        save_path: 저장할 파일 경로 (예: output/logo_1.png)
        timeout: 다운로드 제한 시간 (초)

    Returns:
        저장된 파일 경로
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # 🔍 데이터가 URL인지 Base64인지 판단
    if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
        # 📥 URL 방식: 인터넷에서 다운로드
        response = requests.get(image_data, timeout=timeout, stream=True)
        response.raise_for_status()  # 실패하면 예외 발생

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        # 🔓 Base64 방식: 디코딩해서 저장
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise ValueError(f"Base64 디코딩 실패: {e}")
        
        with open(save_path, "wb") as f:
            f.write(image_bytes)

    return save_path


def save_text(text: str, path: Path) -> None:
    """텍스트를 파일로 저장합니다 (UTF-8 인코딩)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ============================================================
# main.py에서 사용하는 래퍼 함수들
# ============================================================

def load_brief(file_path: str) -> dict:
    """
    브리프 JSON 파일 로드
    (load_json의 래퍼 함수)
    
    Args:
        file_path: 브리프 JSON 파일 경로
        
    Returns:
        dict: 파싱된 브리프 데이터
        
    Raises:
        FileNotFoundError: 파일이 없을 때
        json.JSONDecodeError: JSON 파싱 오류
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    return load_json(path)


def save_result(result: dict, output_path: Path) -> None:
    """
    생성 결과를 JSON 파일로 저장
    (save_json의 래퍼 함수)
    
    Args:
        result: 생성된 결과 딕셔너리
        output_path: 저장할 파일 경로 (Path 객체)
    """
    save_json(result, Path(output_path))