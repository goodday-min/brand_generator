"""
브랜드 슬로건을 생성합니다.
"""
from openai import OpenAI
from utils.llm_client import call_llm_json
from prompts.templates import SLOGAN_SYSTEM, SLOGAN_USER


def generate_slogans(client: OpenAI, brief: dict, naming: dict = None) -> dict:
    """
    브랜드 슬로건 5개를 만듭니다.
    naming 결과가 있으면 첫 번째 이름을 활용합니다.
    """
    # 이름이 있으면 첫 번째 후보 사용, 없으면 힌트 사용
    if naming and naming.get("names"):
        first = naming["names"][0]
        brand_name = f"{first.get('korean', '')} ({first.get('english', '')})"
    else:
        brand_name = brief.get("brand_hint", "(미정)")

    user_prompt = SLOGAN_USER.format(
        brand_name=brand_name,
        industry=brief.get("industry", ""),
        target=brief.get("target", ""),
        tone=brief.get("tone", ""),
        keywords=", ".join(brief.get("keywords", []))
    )

    result = call_llm_json(
        client,
        system_prompt=SLOGAN_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.85
    )

    if "slogans" not in result or not isinstance(result["slogans"], list):
        raise ValueError("AI 응답에 'slogans' 리스트가 없어요.")

    return result
