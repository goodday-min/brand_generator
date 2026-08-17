"""
브랜드 이름 후보를 생성합니다.
"""
from openai import OpenAI
from utils.llm_client import call_llm_json
from prompts.templates import NAMING_SYSTEM, NAMING_USER


def generate_names(client: OpenAI, brief: dict) -> dict:
    """
    브리프를 바탕으로 브랜드 이름 후보 5개를 만듭니다.

    Returns:
        {
          "names": [
            {"korean": "...", "english": "...", "meaning": "...", ...}
          ]
        }
    """
    user_prompt = NAMING_USER.format(
        industry=brief.get("industry", ""),
        target=brief.get("target", ""),
        tone=brief.get("tone", ""),
        keywords=", ".join(brief.get("keywords", [])),
        description=brief.get("description", "(없음)"),
        avoid=brief.get("avoid", "(없음)")
    )

    result = call_llm_json(
        client,
        system_prompt=NAMING_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.9  # 창의성 높게
    )

    # 응답 형식 검증
    if "names" not in result or not isinstance(result["names"], list):
        raise ValueError("AI 응답에 'names' 리스트가 없어요.")

    if len(result["names"]) == 0:
        raise ValueError("생성된 이름이 없어요.")

    return result
