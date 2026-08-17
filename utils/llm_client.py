"""
OpenAI 클라이언트 초기화 + 재시도 로직 래퍼
"""
import os
import time
import json
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
from dotenv import load_dotenv

load_dotenv()


class APIKeyError(Exception):
    """API Key 관련 커스텀 에러"""
    pass


class APIConnectionErr(Exception):
    """네트워크 연결 관련 커스텀 에러"""
    pass


def get_client() -> OpenAI:
    """OpenAI 클라이언트를 만들어 돌려줍니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise APIKeyError(
            "OPENAI_API_KEY가 설정되지 않았어요.\n"
            "   💡 해결 방법: .env 파일에 OPENAI_API_KEY=sk-... 추가하세요."
        )
    return OpenAI(api_key=api_key)


def call_llm_json(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    max_retries: int = 3,
    temperature: float = 0.8
) -> dict:
    """
    LLM을 호출해서 JSON 형식 응답을 받아옵니다.
    - 인증 오류(401): 즉시 중단 (재시도 안 함)
    - 네트워크 오류: 재시도
    - 기타 오류: 재시도
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response.choices[0].message.content
            return json.loads(content)
        
        # 🔴 인증 오류: 재시도 없이 즉시 중단
        except AuthenticationError:
            raise APIKeyError(
                "API Key가 올바르지 않아요.\n"
                "   💡 해결 방법:\n"
                "      1. .env 파일의 OPENAI_API_KEY 값을 확인하세요.\n"
                "      2. https://platform.openai.com/account/api-keys 에서 새 키를 발급받으세요.\n"
                "      3. 키 앞뒤 공백이나 따옴표가 있는지 확인하세요."
            )
        
        # 🟡 요청 한도 초과: 오래 기다린 후 재시도
        except RateLimitError:
            last_error = "요청 한도 초과 (Rate Limit)"
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"   ⏳ API 사용량 한도 초과. {wait}초 후 재시도...")
                time.sleep(wait)
                continue
        
        # 🟠 네트워크 오류: 재시도
        except APIConnectionError:
            last_error = "네트워크 연결 실패"
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"   🌐 네트워크 오류. {wait}초 후 재시도...")
                time.sleep(wait)
                continue
        
        # 🔵 JSON 파싱 오류: 재시도
        except json.JSONDecodeError as e:
            last_error = f"JSON 파싱 실패: {e}"
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"   ⏳ {wait}초 후 재시도... ({attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
        
        # ⚫ 기타 오류: 재시도
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"   ⏳ {wait}초 후 재시도... ({attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue

    raise RuntimeError(f"LLM 호출 {max_retries}회 실패: {last_error}")


def call_image_generation(
    client: OpenAI,
    prompt: str,
    model: str = "gpt-image-1",
    size: str = "1024x1024",
    max_retries: int = 2
) -> str:
    """
    이미지 생성 API를 호출해서 이미지 데이터를 받아옵니다.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                n=1
            )
            
            data = response.data[0]
            
            if hasattr(data, 'b64_json') and data.b64_json:
                return data.b64_json
            
            if hasattr(data, 'url') and data.url:
                return data.url
            
            raise ValueError("이미지 응답에 URL도 Base64 데이터도 없습니다.")
        
        # 🔴 인증 오류: 즉시 중단
        except AuthenticationError:
            raise APIKeyError(
                "API Key가 올바르지 않아요.\n"
                "   💡 .env 파일의 OPENAI_API_KEY를 확인하세요."
            )
        
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                wait = 3 * (attempt + 1)
                print(f"   ⏳ {wait}초 후 재시도...")
                time.sleep(wait)

    raise RuntimeError(f"이미지 생성 실패: {last_error}")