"""
브랜드 스토리(탄생 배경, 미션, 비전, 핵심 가치)를 생성합니다.
"""
from openai import OpenAI
from utils.llm_client import call_llm_json
from prompts.templates import STORY_SYSTEM, STORY_USER


def generate_story(client: OpenAI, brief: dict, naming: dict = None) -> dict:
    """
    브랜드의 탄생 배경, 미션, 비전, 핵심 가치를 담은 스토리를 만듭니다.

    Returns:
        {
          "origin": "...",
          "mission": "...",
          "vision": "...",
          "core_values": [...],
          "summary": "..."
        }
    """
    # 브랜드 이름 결정 (naming 결과 우선, 없으면 힌트)
    if naming and naming.get("names"):
        first = naming["names"][0]
        brand_name = f"{first.get('korean', '')} ({first.get('english', '')})"
    else:
        brand_name = brief.get("brand_hint", "(미정)")

    user_prompt = STORY_USER.format(
        brand_name=brand_name,
        industry=brief.get("industry", ""),
        target=brief.get("target", ""),
        tone=brief.get("tone", ""),
        keywords=", ".join(brief.get("keywords", [])),
        description=brief.get("description", "(없음)")
    )

    result = call_llm_json(
        client,
        system_prompt=STORY_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.75  # 스토리는 일관성이 중요하므로 약간 낮게
    )

    # 필수 필드 검증
    required = ["origin", "mission", "vision", "core_values", "summary"]
    missing = [f for f in required if f not in result]
    if missing:
        raise ValueError(f"스토리 응답에 누락된 항목: {missing}")

    return result