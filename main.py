"""
AI 브랜드 아이덴티티 생성기 - 메인 실행 파일
6단계 파이프라인: 네이밍 → 슬로건 → 스토리 → 팔레트 → 로고 → 경쟁사 분석
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from utils.llm_client import get_client, APIKeyError
from utils.io_helper import load_brief, save_result
from generators.naming import generate_names
from generators.slogan import generate_slogans
from generators.story import generate_story
from generators.palette import generate_palette
from generators.logo import generate_logos
from generators.competitor import analyze_competitors


def run_pipeline(brief: dict, output_dir: Path) -> dict:
    """
    브랜드 생성 6단계 파이프라인 실행
    → 파일 저장 로직은 그대로! 콘솔 출력만 요약 형태로 표시.
    """
    client = get_client()
    result = {
        "brief": brief,
        "generated_at": datetime.now().isoformat(),
        "errors": []
    }

    # ============================================================
    # [1/6] 브랜드 네이밍
    # ============================================================
    print("[1/6] 브랜드 네이밍 생성 중...")
    try:
        result["naming"] = generate_names(client, brief)
        names_list = result["naming"].get("names", [])
        for name_item in names_list:
            kr = name_item.get("korean", "")
            en = name_item.get("english", "")
            meaning = name_item.get("meaning", "")
            
            # 15자 초과 시 잘라내기
            if len(meaning) > 15:
                meaning = meaning[:15] + "..."
            
            print(f"  - {kr} ({en}): {meaning}")
    except APIKeyError:
        raise
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        result["errors"].append(f"naming: {e}")
        result["naming"] = None

    # ============================================================
    # [2/6] 슬로건
    # ============================================================
    print("[2/6] 슬로건 생성 중...")
    try:
        result["slogans"] = generate_slogans(client, brief, result.get("naming"))
        slogans_list = result["slogans"].get("slogans", [])
        for slogan in slogans_list:
            text = slogan.get("text", "")
            lang = slogan.get("language", "")
            print(f'  - "{text}" ({lang})')
    except APIKeyError:
        raise
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        result["errors"].append(f"slogan: {e}")
        result["slogans"] = None

    # ============================================================
    # [3/6] 브랜드 스토리
    # ============================================================
    print("[3/6] 브랜드 스토리 생성 중...")
    try:
        result["story"] = generate_story(client, brief, result.get("naming"))
        
        # summary 글자수만 계산해서 출력
        summary = result["story"].get("summary", "")
        print(f"  ✅ 스토리 생성 완료 ({len(summary)}자)")
        
    except APIKeyError:
        raise
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        result["errors"].append(f"story: {e}")
        result["story"] = None

    # ============================================================
    # [4/6] 컬러 팔레트
    # ============================================================
    print("[4/6] 컬러 팔레트 생성 중...")
    try:
        result["palette"] = generate_palette(client, brief, output_dir)
        palette_data = result["palette"]
        colors = palette_data.get("colors", [])
        
        # role별로 분류해서 출력
        for color in colors:
            role = color.get("role", "")
            name = color.get("name", "")
            hex_code = color.get("hex", "")
            print(f"  - [{role}] {hex_code} ({name})")
        
        # 저장 경로 안내
        image_path = palette_data.get("image_path", "")
        if image_path:
            print(f"  💾 저장: {image_path}")
    except APIKeyError:
        raise
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        result["errors"].append(f"palette: {e}")
        result["palette"] = None

    # ============================================================
    # [5/6] 로고 시안
    # ============================================================
    print("[5/6] 로고 시안 생성 중...")
    try:
        result["logos"] = generate_logos(
            client, brief,
            result.get("naming"),
            result.get("palette"),
            output_dir
        )
        logos_list = result["logos"] if isinstance(result["logos"], list) else []
        for idx, logo in enumerate(logos_list, 1):
            if isinstance(logo, dict):
                style = logo.get("style", "")
                image_path = logo.get("image_path", "")
                # 스타일 앞부분만 짧게
                style_short = style.split(",")[0] if style else f"로고 {idx}"
                print(f"  - [{idx}] {style_short}")
                if image_path:
                    print(f"        💾 {image_path}")
    except APIKeyError:
        raise
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        result["errors"].append(f"logo: {e}")
        result["logos"] = None

    # ============================================================
    # [6/6] 경쟁사 분석
    # ============================================================
    print("[6/6] 경쟁사 분석 중...")
    try:
        result["competitors"] = analyze_competitors(client, brief)
        comp_data = result["competitors"]
        
        # 방어적 처리 (구조 다양성 대응)
        if isinstance(comp_data, dict):
            comp_list = comp_data.get("competitors", []) or comp_data.get("list", [])
        else:
            comp_list = comp_data if isinstance(comp_data, list) else []
        
        for comp in comp_list:
            if isinstance(comp, dict):
                name = comp.get("name", "")
                feature = (comp.get("feature") or comp.get("summary") 
                          or comp.get("description") or comp.get("positioning", ""))
                # 길면 자르기
                if len(feature) > 40:
                    feature = feature[:40] + "..."
                print(f"  - {name}: {feature}")
            else:
                print(f"  - {comp}")
    except APIKeyError:
        raise
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        result["errors"].append(f"competitor: {e}")
        result["competitors"] = None

    return result


def interactive_input():
    """대화형 입력 모드"""
    print("=" * 60)
    print("🎨 AI 브랜드 아이덴티티 생성기")
    print("=" * 60)
    
    # 브리프 파일 경로
    default_brief = "brief.json"
    brief_input = input(f"📄 브리프 파일 경로 (기본값: {default_brief}): ").strip()
    brief_path = brief_input if brief_input else default_brief
    
    # 출력 폴더
    default_output = "output"
    output_input = input(f"📁 출력 폴더 (기본값: {default_output}): ").strip()
    output_base = output_input if output_input else default_output
    
    return brief_path, output_base


def main():
    parser = argparse.ArgumentParser(description="AI 브랜드 아이덴티티 생성기")
    parser.add_argument("--brief", type=str, help="브리프 JSON 파일 경로")
    parser.add_argument("--output", type=str, default="output", help="출력 폴더 경로")
    parser.add_argument("--interactive", "-i", action="store_true", help="대화형 입력 모드")
    args = parser.parse_args()

    # 입력 방식 결정
    if args.interactive or not args.brief:
        brief_path, output_base = interactive_input()
    else:
        brief_path = args.brief
        output_base = args.output

    # 브리프 로드
    try:
        brief = load_brief(brief_path)
    except FileNotFoundError:
        print(f"❌ 브리프 파일을 찾을 수 없습니다: {brief_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        sys.exit(1)

    # 출력 폴더 생성 (브랜드힌트_타임스탬프)
    brand_hint = brief.get("brand_hint", "brand")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_base) / f"{brand_hint}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 출력 폴더: {output_dir}\n")

    # 파이프라인 실행
    try:
        result = run_pipeline(brief, output_dir)
    except APIKeyError as e:
        print(f"\n❌ API 키 오류: {e}")
        print("💡 .env 파일에 OPENAI_API_KEY를 설정하세요.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자 중단됨")
        sys.exit(0)

    # 결과 저장
    result_path = output_dir / "result.json"
    save_result(result, result_path)
    
    print("\n" + "=" * 60)
    print(f"✅ 완료! 결과 저장: {result_path}")
    print(f"📊 오류: {len(result.get('errors', []))}개")
    print("=" * 60)


if __name__ == "__main__":
    main()