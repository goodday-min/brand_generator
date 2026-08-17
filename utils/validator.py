"""
브리프(입력 JSON)의 필수 항목이 모두 있는지 검사합니다.
"""
from typing import Tuple, List


# 반드시 있어야 하는 항목 목록
REQUIRED_FIELDS = [
    "industry",       # 업종 (예: "친환경 화장품")
    "target",         # 타겟 고객 (예: "20-30대 여성")
    "tone",           # 브랜드 톤 (예: "따뜻하고 신뢰감 있는")
    "keywords",       # 핵심 키워드 리스트
]

# 있으면 좋은 선택 항목
OPTIONAL_FIELDS = [
    "brand_hint",     # 브랜드명 힌트 (파일명에 사용)
    "description",    # 추가 설명
    "avoid",          # 피하고 싶은 이미지
]


def validate_brief(brief: dict) -> Tuple[bool, List[str]]:
    """
    브리프를 검사해서 (유효한지, 오류 목록)을 돌려줍니다.

    Returns:
        (True, []) - 문제 없음
        (False, ["오류1", "오류2"]) - 문제 있음
    """
    errors = []

    # 딕셔너리 형태인지 확인
    if not isinstance(brief, dict):
        return False, ["브리프는 JSON 객체(딕셔너리) 형태여야 해요."]

    # 필수 항목 존재 여부 확인
    for field in REQUIRED_FIELDS:
        if field not in brief:
            errors.append(f"필수 항목 누락: '{field}'")
            continue

        value = brief[field]
        # 빈 값 체크
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"'{field}' 값이 비어있어요.")
        elif isinstance(value, list) and len(value) == 0:
            errors.append(f"'{field}' 리스트가 비어있어요.")

    # keywords는 리스트 형태여야 함
    if "keywords" in brief and not isinstance(brief["keywords"], list):
        errors.append("'keywords'는 리스트 형태여야 해요. 예: [\"자연\", \"순수\"]")

    return len(errors) == 0, errors
