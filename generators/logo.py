"""
gpt-image-1 를 사용해 브랜드 로고 이미지 시안을 생성합니다.
"""
import base64  # 파일 상단 import에 추가
from pathlib import Path
from openai import OpenAI


from utils.llm_client import call_image_generation
from utils.io_helper import download_image
from prompts.templates import LOGO_PROMPT_TEMPLATE, LOGO_STYLE_VARIATIONS


def generate_logos(
    client: OpenAI,
    brief: dict,
    naming: dict = None,
    palette: dict = None,
    output_dir: Path = None
) -> list:
    """
    다양한 스타일의 로고 시안을 여러 개 생성합니다.

    Returns:
        [
          {"style": "...", "prompt": "...", "url": "...", "file_path": "..."},
          ...
        ]
    """
    # 브랜드명 결정
    if naming and naming.get("names"):
        first = naming["names"][0]
        brand_name = first.get("english") or first.get("korean") or "Brand"
    else:
        brand_name = brief.get("brand_hint", "Brand")

    # 색상 결정 (팔레트 있으면 활용)
    main_color = "#333333"
    accent_color = "#666666"
    if palette and palette.get("colors"):
        for c in palette["colors"]:
            role = c.get("role", "").lower()
            if "main" in role:
                main_color = c.get("hex", main_color)
            elif "accent" in role:
                accent_color = c.get("hex", accent_color)

    results = []

    # 스타일 변형별로 로고 생성
    for idx, style_variation in enumerate(LOGO_STYLE_VARIATIONS, start=1):
        print(f"   🎨 로고 시안 {idx}/{len(LOGO_STYLE_VARIATIONS)} 생성 중...")

        prompt = LOGO_PROMPT_TEMPLATE.format(
            brand_name=brand_name,
            industry=brief.get("industry", ""),
            tone=brief.get("tone", ""),
            main_color=main_color,
            accent_color=accent_color,
            keywords=", ".join(brief.get("keywords", [])),
            extra_style=style_variation
        )

        try:
            image_url = call_image_generation(client, prompt)

            # 이미지 다운로드
            file_path = output_dir / f"logo_{idx}.png"
            download_image(image_url, file_path)

            results.append({
                "style": style_variation,
                "prompt": prompt,
                "url": image_url,
                "file_path": str(file_path)
            })
            print(f"      ✅ 저장: {file_path.name}")

        except Exception as e:
            print(f"      ⚠️ 시안 {idx} 실패: {e}")
            results.append({
                "style": style_variation,
                "prompt": prompt,
                "error": str(e)
            })

    if not any("file_path" in r for r in results):
        raise RuntimeError("모든 로고 시안 생성이 실패했어요.")

    return results
