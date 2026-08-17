"""
업종의 주요 경쟁사와 차별화 전략을 분석합니다. (선택 기능)
"""
from openai import OpenAI
from utils.llm_client import call_llm_json
from prompts.templates import COMPETITOR_SYSTEM, COMPETITOR_USER


def analyze_competitors(client: OpenAI, brief: dict) -> dict:
    """
    경쟁사 3곳을 조사하고 우리 브랜드의 차별화 전략을 제안합니다.

    Returns:
        {
          "competitors": [...],
          "market_trends": [...],
          "differentiation": [...]
        }
    """
    user_prompt = COMPETITOR_USER.format(
        industry=brief.get("industry", ""),
        target=brief.get("target", ""),
        tone=brief.get("tone", ""),
        keywords=", ".join(brief.get("keywords", []))
    )

    result = call_llm_json(
        client,
        system_prompt=COMPETITOR_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.6  # 분석은 팩트 기반이므로 낮게
    )

    # 필수 필드 검증
    required = ["competitors", "market_trends", "differentiation"]
    missing = [f for f in required if f not in result]
    if missing:
        raise ValueError(f"경쟁사 분석 응답에 누락된 항목: {missing}")

    return result
