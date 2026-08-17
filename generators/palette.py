"""
브랜드 컬러 팔레트를 생성하고 시각화 이미지를 저장합니다.
"""
from pathlib import Path
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

from utils.llm_client import call_llm_json
from prompts.templates import PALETTE_SYSTEM, PALETTE_USER


def generate_palette(client: OpenAI, brief: dict, output_dir: Path) -> dict:
    """
    색상 팔레트를 만들고 팔레트 이미지(palette.png)를 저장합니다.
    """
    user_prompt = PALETTE_USER.format(
        industry=brief.get("industry", ""),
        target=brief.get("target", ""),
        tone=brief.get("tone", ""),
        keywords=", ".join(brief.get("keywords", []))
    )

    result = call_llm_json(
        client,
        system_prompt=PALETTE_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.7
    )

    if "colors" not in result or not isinstance(result["colors"], list):
        raise ValueError("AI 응답에 'colors' 리스트가 없어요.")

    # HEX 코드 유효성 간단 검증
    for c in result["colors"]:
        hex_code = c.get("hex", "")
        if not (hex_code.startswith("#") and len(hex_code) == 7):
            raise ValueError(f"올바르지 않은 HEX 코드: {hex_code}")

    # 팔레트 이미지 생성
    image_path = output_dir / "palette.png"
    _draw_palette_image(result["colors"], image_path)
    result["image_path"] = str(image_path)

    return result


def _draw_palette_image(colors: list, save_path: Path) -> None:
    """
    색상 리스트를 받아 팔레트 이미지를 그립니다.
    각 색상 아래에 이름과 HEX 코드를 표시합니다.
    """
    swatch_width = 200
    swatch_height = 250
    text_area = 80
    total_width = swatch_width * len(colors)
    total_height = swatch_height + text_area

    # 흰 배경 이미지 생성
    img = Image.new("RGB", (total_width, total_height), "white")
    draw = ImageDraw.Draw(img)

    # 폰트 로드 (시스템 기본 폰트 사용, 실패 시 기본 폰트)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 각 색상 사각형 그리기
    for i, color in enumerate(colors):
        x = i * swatch_width
        hex_code = color.get("hex", "#000000")
        name = color.get("name", "")
        role = color.get("role", "")

        # 색상 사각형
        draw.rectangle(
            [x, 0, x + swatch_width, swatch_height],
            fill=hex_code
        )

        # 텍스트 (색상명, 역할, HEX)
        text_y = swatch_height + 10
        draw.text((x + 10, text_y), name, fill="black", font=font)
        draw.text((x + 10, text_y + 25), role, fill="gray", font=font_small)
        draw.text((x + 10, text_y + 45), hex_code, fill="black", font=font_small)

    img.save(save_path)
