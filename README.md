# 🎨 AI 브랜드 아이덴티티 생성기 (AI Brand Identity Generator)

브랜드 브리프(업종, 타겟, 키워드 등 : JSON) 하나만 입력하면,   
LLM API와 이미지 생성 API를 조합하여 **브랜드 네이밍 · 슬로건 · 브랜드 스토리 · 컬러 팔레트 · 로고 시안**까지 자동으로 생성해주는  
CLI 기반 Python 프로그램입니다.

```

브랜드 브리프(JSON) → [LLM API + 이미지 생성 API] → 브랜드 아이덴티티 결과 파일저장(텍스트 + 이미지)

```
---

## 📌 프로젝트 소개

  업종·타겟·키워드 등 브랜드 정보를 JSON 파일로 입력 받으면, LLM API로 텍스트 기반 브랜드 요소(네이밍/슬로건/스토리/컬러)를 생성하고,   
  이미지 생성 API로 로고 시안까지 만든 뒤 모든 결과물을 지정된 폴더 하나에 JSON과 PNG 형태로 저장합니다.   
  이 프로젝트는 브랜드 아이덴티티를 만드는 과정을 **브리프 하나로 자동화**하는 것을 목표로 합니다. 

  이번 구현에서는 텍스트 생성에 **OpenAI GPT API**, 로고 이미지 생성에 **OpenAI 이미지 생성 API(gpt-image-1)** 를 사용합니다.

---

## 📌 과제 목표

이 과제를 완료하면 아래 4가지를 스스로 설명할 수 있어야 합니다. 
각 목표를 이 프로젝트에서 어떻게 구현했는지 함께 정리했습니다.

| # | 학습 목표 | 이 프로젝트에서의 구현 위치 |
|---|---|---|
| 1 | 브랜드 브리프를 입력받아 AI로 브랜드 요소를 생성하는 파이프라인을 설명할 수 있다 | `main.py`의 `run_pipeline()` — 5단계 파이프라인으로 구현 |
| 2 | LLM API와 이미지 생성 API를 조합해 텍스트+이미지 결과물을 생성하는 방법을 설명할 수 있다 | `utils/llm_client.py`의 `chat_json()`(텍스트) / `generate_image_b64()`(이미지) |
| 3 | 생성된 컬러 팔레트를 시각화하여 이미지로 저장하는 방법을 설명할 수 있다 | `generators/palette.py`의 `visualize_palette()` (matplotlib 활용) |
| 4 | API 호출 시 발생할 수 있는 오류 상황과 대응 방법을 설명할 수 있다 | `utils/llm_client.py`의 `call_with_retry()` + 단계별 개별 `try-except` → 📌[8장](#8-api-오류-상황과-대응-방법) 참고📌 |


---

## 📌 기능 요구사항

| # | 기 능 | 상세 내용 | 구현 파일 |
|---| :--- |---|---|
| 1 | 사용자 입력 | `input()`으로 브리프 파일 경로(필수), 출력 폴더 경로(선택, 기본값 `./output`)를 대화형으로 입력받음 | `main.py` |
| 2 |  브랜드 브리프 입력  | JSON 파일 로드. 필수 필드 `industry`, `target`, `keywords` / 선택 필드 `tone`, `competitors`, `notes` | `utils/io_helper.py`, `utils/validator.py` |
| 3 |  브랜드 네이밍 생성  | LLM API 호출 → 네이밍 후보 3~5개 + 각 네이밍의 의미/유래 생성 (한글 15자 이내 제약) | `generators/naming.py` |
| 4 | 슬로건 생성 | LLM API 호출 → 톤앤매너에 맞는 슬로건/태그라인 3개 생성 | `generators/slogan.py` |
| 5 |  브랜드 스토리 생성  | LLM API 호출 → 탄생 배경·철학·비전이 담긴 스토리 300자 내외 생성 | `generators/story.py` |
| 6 | 컬러 팔레트 생성 | LLM API 호출 → 메인 컬러 1개 + 서브 컬러 2~3개(HEX) 추천, matplotlib으로 시각화 후 PNG 저장 | `generators/palette.py` |
| 7 | 로고 시안 생성 | 이미지 생성 API(`gpt-image-1`) 호출 → 로고 시안 2~3개를 PNG로 저장 | `generators/logo.py` |
| 8 | 결과 저장 | 텍스트 결과는 `brand_result.json`, 이미지는 개별 PNG로 출력 폴더에 저장 | `utils/io_helper.py` |
| 9 | 에러 처리 | 각 단계를 개별 `try-except`로 감싸 하나가 실패해도 다음 단계 계속 진행, 실패 내역은 `errors` 필드에 기록 | `main.py` |
| 10 | API 키 관리 | 코드에 키를 직접 작성하지 않고 `.env` 파일 + `python-dotenv`로 환경변수에서 로드 | `utils/llm_client.py`, `.env` |

---

## 📌 시스템 아키텍처 / 파이프라인

```
┌─────────────────────────────────────────────┐
│ ① 사용자 입력 (CLI)                          │
│   - 브리프 JSON 파일 경로                    │
│   - 출력 폴더 경로 (기본값: ./output)        │
└──────────────────┬────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ ② 브리프 로드 & 검증                         │
│   - JSON 파싱 (utils/io_helper.py)           │
│   - 필수 필드 확인 (utils/validator.py)      │
└──────────────────┬────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ ③ LLM API 호출 (단계별 개별 try-except)      │
│   [1/5] 네이밍 3~5개 (한글+영문+의미)        │
│   [2/5] 슬로건 3개                           │
│   [3/5] 브랜드 스토리 (300자)                │
│   [4/5] 컬러 팔레트 (메인1 + 서브2~3, HEX)   │
│   (보너스) 경쟁사 차별화 분석                │
└──────────────────┬────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ ④ Image API 호출                             │
│   [5/5] 로고 시안 2개 (gpt-image-1)          │
└──────────────────┬────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ ⑤ 시각화 & 저장                              │
│   - matplotlib → color_palette.png           │
│   - base64 디코딩 → logo_01.png, logo_02.png │
│   - 텍스트 결과 → brand_result.json          │
└─────────────────────────────────────────────┘
```

💡 **왜 이렇게 나눴나?**

> | 설계 결정 | 이유 |
> |---|---|
> | 입력/검증을 가장 먼저 분리 | 잘못된 입력을 조기에 걸러 불필요한 API 비용 낭비 방지 |
> | 단계별 개별 `try-except` | 하나의 API 호출이 실패해도 나머지는 계속 진행 → 사용자 경험 향상 |
> | 텍스트 생성 이후에 이미지 생성 | 이미지 API가 상대적으로 비싸고 느리므로, 텍스트(네이밍)가 확보된 뒤에 로고 프롬프트에 반영 |
> | 저장을 마지막 단계로 | 중간에 일부가 실패해도 성공한 결과만이라도 파일로 남길 수 있음 |

---

## 📌 입력 / 출력 스펙

### 📥 입력: `brief.json`

| 필드 | 필수 | 타입 | 설명 | 예시 |
|---|---|---|---|---|
| `industry` | ✅ | string | 업종 | `"친환경 화장품"` |
| `target` | ✅ | string | 타겟 고객 | `"20~30대 여성"` |
| `tone` | ⬜ | string | 톤앤매너 | `"미니멀하고 따뜻한"` |
| `keywords` | ✅ | array | 핵심 키워드 | `["자연", "순수", "지속가능"]` |
| `competitors` | ⬜ | array | 경쟁사 (입력 시 보너스 분석 실행) | `["Aesop", "Innisfree"]` |
| `notes` | ⬜ | string | 추가 요청사항 | `"MZ세대 가치 소비 반영"` |

### 📤 출력 폴더 구조

```
output/
├── result.json          # 모든 텍스트 결과 + 메타데이터
├── palette.png          # 컬러 팔레트 시각화
├── logo_1.png           # 로고 시안 1
└── logo_2.png           # 로고 시안 2
└── logo_3.png           # 로고 시안 3

```

### 📄 출력 : `result.json` 스키마

```json
{
  "brief": { "industry": "...", "target": "...", "keywords": ["..."] },
  "naming": [
    {"ko": "블루밍", "en": "Blooming", "meaning": "자연에서 피어나는 아름다움"}
  ],
  "slogans": ["일상에 자연을 담다", "피부가 숨쉬는 순간", "자연 그대로, 당신 그대로"],
  "story": "브랜드 스토리 본문...",
  "palette": {
    "main": {"hex": "#2E7D32", "name": "Forest Green", "reason": "..."},
    "sub": [{"hex": "#81C784", "name": "Light Green", "reason": "..."}]
  },
  "competitor_analysis": { "competitor_analysis": [...], "differentiation": [...] },
  "generated_at": "2026-08-16T10:30:00",
  "errors": []
}
```


---

## 📌 기술 스택 

| 구분 | 라이브러리 / 도구 | 용도 |
|---|---|---|
| 언어 | Python 3.9+ | CLI 프로그램 |
| LLM API | `openai` (`gpt-4o-mini`) | 네이밍/슬로건/스토리/팔레트/경쟁사 분석 텍스트 생성 |
| 이미지 생성 API | `openai` (`gpt-image-1`) | 로고 시안 생성 |
| 환경변수 관리 | `python-dotenv` | `.env` 파일에서 API 키 로드 |
| 시각화 | `matplotlib` | 컬러 팔레트 PNG 생성 |
| 표준 라이브러리 | `json`, `os`, `pathlib`, `datetime`, `base64`, `sys`, `time` | 파싱/저장/경로 처리/재시도 로직 등 |

> 💡 **왜 `gpt-image-1`인가?**   
>  과제 문서에는 예시로 DALL·E가 언급되어 있지만, 개발 시점 기준 `dall-e-3`는 신규 모델로 대체되는 추세이며
>  `gpt-image-1`은 별도의 `response_format` 파라미터 없이 기본적으로 `b64_json` 형식을 반환해 URL 다운로드 없이 바로 파일로 저장할 수 있다는 
>  실무적 장점이 있습니다.

#### 🛠️ 핵심 라이브러리

| 라이브러리 | 하는 일 | 꼭 필요한가? |
|-----------|---------|-------------|
| `openai` | LLM & 이미지 생성 API 사용 | ✅ 꼭 필요 |
| `python-dotenv` | API 키 안전하게 관리 | ✅ 꼭 필요 |
| `matplotlib` | 색상 팔레트 그리기 | ✅ 꼭 필요 |
| `requests` | 이미지 URL에서 다운로드 | ✅ 꼭 필요 |
| `Pillow` | 이미지 추가 가공 | ⭕ 선택 |
| `rich` | 예쁜 CLI 화면 출력 | ⭕ 선택 |

#### 🐍 Python 기본 기능 활용

| 기본 기능 | 하는 일 |
|-----------|---------|
| `json` | JSON 파일 읽고 쓰기 |
| `os` | 환경변수 읽기, 폴더 만들기 |
| `pathlib` | 파일 경로 다루기 (권장) |
| `datetime` | 결과 생성 시각 기록 |
| `sys` | 프로그램 종료 코드 처리 |

---

## 📌 프로젝트 구조

```
brand_generator/
│
├── main.py                    # 🚪 CLI 진입점 (파이프라인 오케스트레이션)
│
├── generators/                # 🤖 AI 생성 모듈 (기능 하나당 파일 하나)
│   ├── __init__.py 
│   ├── naming.py              # 네이밍 생성 (한글/영문 + 의미)
│   ├── slogan.py              # 슬로건 생성
│   ├── story.py               # 브랜드 스토리 생성
│   ├── palette.py             # 컬러 팔레트 생성 + matplotlib 시각화
│   ├── logo.py                # 로고 이미지 생성
│   └── competitor.py          # 경쟁사 분석 [보너스]
│
├── utils/                      # 🛠️ 공통 유틸리티
│   ├── __init__.py
│   ├── io_helper.py            # JSON 로드/저장, 이미지 저장, 폴더 생성
│   ├── llm_client.py           # OpenAI 클라이언트 + 재시도 로직 래퍼
│   └── validator.py            # 브리프 필수 필드 검증
│
├── prompts/                    # 📝 프롬프트 템플릿 분리
│   ├── __init__.py
│   └── templates.py
│
├── output/                      # 결과물 저장 폴더 (git 제외)
├── .env                         # 🔑 실제 API 키 (git 제외)
├── .env.example                 # 🔑 API 키 템플릿 (git 포함)
├── .gitignore                   # Git 추적 제외 파일
├── brief_example.json           # 📄 예시 브리프
├── requirements.txt              # 📦 의존성 목록
└── readme_nato.md                # 📖 이 문서
```

💡 **왜 이렇게 나눴을까?**

> | 원칙 | 설명 | 적용 |
> |---|---|---|
> | 단일 책임 원칙 | 파일 하나 = 역할 하나 | `naming.py`는 네이밍 생성만 담당 |
> | 관심사 분리 | 로직 / 설정 / 프롬프트 분리 | `generators/`, `utils/`, `prompts/` |
> | 재사용성 | 공통 코드는 `utils`로 | LLM/이미지 호출 코드는 `llm_client.py` 하나에 집중 |
> | 확장성 | 새 생성기 = 새 파일 하나 추가 | 예: 홍보 문구 생성기를 추가하려면 `generators/promo.py`만 추가하면 됨 |

### ✅ 주요 설계 결정

|  결  정  사  항  | 선택한 방식 | 이유 |
|      ---      |---|---|
| 이미지<br>생성 모델 | `dall-e-3` 대신 `gpt-image-1` 채택 | ① **실무적 이유**: 개발 시점 기준 OpenAI 이미지 생성 라인업이<br> `gpt-image-1`로 이전되는 추세였고, 실제로 `dall-e-3`로 개발 중<br>모델 단종(retire) 이슈를 겪어 전환함 <br> ② **코드 단순화**: `dall-e-3`는 `response_format`(`url`/`b64_json`)<br>지정이 필요하고 `url` 방식이면 `requests.get()` 재다운로드 단계가<br>추가되지만, `gpt-image-1`은 해당 파라미터 없이 기본 `b64_json`을 반환해 `base64.b64decode()` 한 번으로 PNG 저장이 끝남(실패 지점 감소) <br> ③ **API 키 통합 관리**: 텍스트(`gpt-4o-mini`)와 이미지가 동일한<br>`OPENAI_API_KEY`로 호출되어 별도 계정 없이 하나의 키로<br>파이프라인 전체를 관리 가능 |
| 파이프라인 실행 순서 | 텍스트 생성<br>(네이밍→슬로건→스토리→팔레트) 이후<br>이미지(로고) 생성 | 이미지 API가 상대적으로 비싸고 느리므로, 텍스트(특히 네이밍/컬러)가<br>먼저 확보된 뒤 그 결과를 로고 프롬프트에 반영해 일관성을 높임 |
| 저장 시점 | 모든 단계 실행 후 마지막에 일괄 저장 | 중간에 일부 단계가 실패해도 성공한 결과만이라도 파일로 남길 수 있도록 함 |
| 네이밍 글자 수 제약 | 프롬프트 지시 + 코드 레벨<br>하드 트렁케이션(15자) 이중 적용 | 프롬프트만으로는 LLM이 제약을 100% 지키지 않는 경우가 있어,<br>코드로 안전망을 추가함 ("이중 안전망" 원칙) |
| 에러 처리 단위 | 단계별(naming/slogan/story/palette/logo)<br>개별 `try-except` | 하나의 API 호출이 실패해도 전체 파이프라인이 중단되지 않고<br>나머지 단계가 계속 진행되도록 함 |

---

## 📌 API 오류 상황과 대응 방법

> 실제 이 프로젝트가 각 오류 상황에 어떻게 대응하도록 구현되었는지 정리한 표입니다.

| 오류 유형 | 발생 원인 | 이 프로젝트의 대응 방법 | 관련 코드 |
|---|---|---|---|
| 인증 오류 (401) | API 키가 없거나 잘못됨/만료됨 | 프로그램 시작 시 키 존재 여부를 먼저 검증하고, 없으면 명확한 안내 메시지 출력 후 즉시 종료 | `llm_client.get_client()` |
| 요청 초과 (429 Rate Limit) | 짧은 시간에 너무 많은 요청 | 지수 백오프(exponential backoff) 방식으로 최대 3회까지 자동 재시도 | `llm_client.call_with_retry()` |
| 서버 오류 (5xx) | OpenAI 서버 측 일시적 문제 | 동일하게 재시도 로직 적용, 최종 실패 시 예외를 상위로 전달 | `llm_client.call_with_retry()` |
| 네트워크 오류 | 인터넷 연결 불안정, 타임아웃 | 재시도 로직으로 1차 대응, 반복 실패 시 해당 단계만 건너뛰고 다음 단계 진행 | `main.run_pipeline()`의 단계별 `try-except` |
| JSON 파싱 오류 | LLM이 형식을 지키지 않고 설명글을 덧붙임 | `response_format={"type": "json_object"}`로 JSON 모드 강제 + 파싱 실패 시 별도 예외로 감지 | `llm_client.chat_json()` |
| 브리프 파일 오류 | 파일 경로가 잘못되었거나 JSON 형식이 아님 | 파일 존재 여부와 JSON 파싱을 먼저 검증하고, 실패 시 즉시 종료 (API 호출 전 단계이므로 재시도 대상 아님) | `io_helper.load_brief()` |
| 필수 필드 누락 | 브리프에 `industry`/`target`/`keywords` 중 하나라도 없음 | 어떤 필드가 빠졌는지 구체적으로 안내하고 프로그램 종료 | `validator.validate_brief()` |
| 파일 저장(I/O) 오류 | 출력 폴더 권한 없음, 디스크 공간 부족 | 출력 폴더를 파이프라인 실행 전 미리 생성(`mkdir(parents=True, exist_ok=True)`)해 경로 문제를 사전 차단 | `io_helper.ensure_output_dir()` |

### ✅ 오류 처리 계층 구조

```
1. 프로그램 시작 전
   - API 키 존재 검증 → 실패 시 즉시 종료
   - 브리프 파일 존재/형식 검증 → 실패 시 즉시 종료
        ↓
2. 각 생성 단계 (naming / slogan / story / palette / logo)
   - 개별 try-except로 감싸기
   - 재시도(최대 3회, 지수 백오프) 후에도 실패하면 해당 단계만 스킵
   - 실패 내역을 results["errors"]에 기록
        ↓
3. 저장 단계
   - 성공한 결과만이라도 brand_result.json에 저장
   - 어떤 단계가 왜 실패했는지 "errors" 필드로 확인 가능
```

### ✅ 핵심 설계: "부분 실패를 허용하는 파이프라인"

```python
# 나쁜 예 - 하나 실패하면 전체가 중단됨
try:
    naming = generate_naming(brief)
    slogans = generate_slogans(brief)
    story = generate_story(brief)
except Exception as e:
    print(f"실패: {e}")   # 성공한 결과까지 전부 날아감

# 좋은 예 - 이 프로젝트가 채택한 방식
try:
    results["naming"] = generate_naming(brief)
except Exception as e:
    results["naming"] = None
    results["errors"].append({"step": "naming", "error": str(e)})
# 다음 단계(슬로건 생성)는 그대로 계속 진행된다
```

---

## 📌 프롬프트 엔지니어링 원칙

| 원칙 | 설명 | 이 프로젝트 적용 예 |
|---|---|---|
| ① 역할 부여 | AI에게 전문가 역할 부여 | `"당신은 15년 경력의 브랜딩 전문가입니다"` (`prompts/templates.py`의 `SYSTEM_BASE`) |
| ② 명확한 지시 | 무엇을, 몇 개, 어떻게 요청하는지 명시 | `"네이밍 3~5개를 생성하세요"` |
| ③ 컨텍스트 제공 | 브리프 정보(업종/타겟/키워드/톤)를 프롬프트에 포함 | 모든 `*_prompt()` 함수가 `brief` dict를 받아 문자열에 삽입 |
| ④ 출력 형식 지정 | JSON 스키마를 예시로 명시 + `response_format` 강제 | `chat_json()`에서 `response_format={"type": "json_object"}` 사용 |
| ⑤ 제약 조건 | 글자 수, 언어, 금지사항 명시 | `"한글명은 15자 이내"`, `"300자 내외"` 등 |

**이중 안전망**: 프롬프트로 "15자 이내"를 요청해도 LLM이 가끔 지키지 않는 경우가 있어,
`generators/naming.py`에서 15자를 초과하면 코드 레벨에서 강제로 잘라내는 안전망을 추가로 두었습니다.
(프롬프트 엔지니어링만으로 100% 제어할 수 없는 부분은 코드로 보완한다는 원칙)

---

## 📌 보너스 과제

| 보너스 기능 | 구현 방식 |
|---|---|
| 경쟁사 분석 추가 | 브리프에 `competitors` 필드가 있을 때만 `generators/competitor.py`가 실행되어, 경쟁사별 포지셔닝 요약과 차별화 전략 3~5가지를 생성 |
| 다국어 네이밍 지원 | 네이밍 생성 단계에서 처음부터 한글명(`ko`)과 영문명(`en`)을 함께 생성하도록 프롬프트/스키마 설계 |


## 📌 실행 방법 & 실행 예시


```bash
# 1) 가상환경 활성화 (STEP 3 참고)
source venv/bin/activate


# 2) 프로그램 실행
python main.py


# 3) 안내에 따라 입력
브리프 파일 경로를 입력하세요: brief.json
출력 폴더 경로를 입력하세요 (엔터 시 ./output): 

```

브랜드 브리프 입력 : JSON(brief.json) 파일로 브랜드 정보(업종, 타켓, 키웓, 톤앤매너등)를 입력 받는다.

입력 파일 예시(brief.json)
{
  "industry": "스페셜티 커피 전문점",
  "target": "20~30대 직장인, 원두 품질을 중시하는 커피 애호가",
  "keywords": ["신선함", "정직한 원두", "따뜻한 공간", "로컬"],
  "tone": "친근하지만 전문적인, 감성적인",
  "competitors": "블루보틀, 프릳츠커피컴퍼니",
  "notes": "동네 골목상권에 위치한 소규모 로스터리 카페입니다. 과하지 않은 편안한 느낌을 원해요."
}



```

### 실행 결과 예시

- 정상 화면
<img width="779" height="673" alt="image" src="https://github.com/user-attachments/assets/4d18f2dd-ac78-48ca-831f-b566f6db9c03" />

-- /output
<img width="487" height="238" alt="image" src="https://github.com/user-attachments/assets/01a0adb4-7094-4caa-854e-eeab1f9660c0" />
<img width="554" height="203" alt="image" src="https://github.com/user-attachments/assets/37e28edc-d3e5-468b-8b4f-b53b9a29fdc2" />

-- / 2026-08-14
<img width="604" height="213" alt="image" src="https://github.com/user-attachments/assets/7aee3b2e-7c5b-4109-af09-4e0952cb325a" />



```
> API 호출이 실패하는 단계가 있어도(예: 네트워크 오류, 키 인증 실패 등) 해당 단계의 실패
> 메시지만 출력되고 나머지 단계는 계속 진행됩니다.
실행이 끝나면 `output/` 폴더(또는 직접 지정한 폴더)에 아래 파일들이 생성됩니다.

- `brand_result.json` — 네이밍, 슬로건, 스토리, 컬러 정보, 생성된 파일 목록
- `color_palette.png` — 컬러 팔레트 시각화 이미지
- `logo_01.png`, `logo_02.png`, `logo_03.png` — AI가 생성한 로고 시안




### 부분 실패 시 예시

```
[2/5] 슬로건 생성 중...
      ⚠️  슬로건 생성 재시도 1/2 (2초 대기 후 재시도) - 사유: ...
      ❌ 슬로건 생성 실패: LLM 응답 JSON 파싱 실패

...(나머지 단계는 계속 진행)...

⚠️  일부 단계가 실패했지만, 성공한 결과는 저장되었습니다.
📋 실패 로그: output/brand_result.json 의 "errors" 필드 확인
```

---










---

## 📌 개발 환경 설정 가이드 

> 이 섹션은 최종 결과물에는 포함되지 않지만, 처음 개발 환경을 세팅하는 분들을 위해
> 순서대로 따라 하면 되는 형태로 정리했습니다.

### Step 1. Python 설치 확인

```bash
python --version
# 또는
python3 --version
```

- 3.9 이상이면 OK. 없다면 [python.org](https://www.python.org/downloads/)에서 설치 (설치 시 "Add Python to PATH" 체크 필수, Windows 기준)

### Step 2. 프로젝트 폴더로 이동

```bash
cd brand_generator
```

### Step 3. 가상환경(venv) 생성 및 활성화

✅ 가상환경(venv)이란?

- **정의**: 파이썬 설치 위에 독립적인 환경을 만드는 기능.  
  각 환경은 자체적인 **파이썬 인터프리터와 site-packages 디렉터리**를 가짐.
- **역할**: 특정 프로젝트에서만 필요한 라이브러리 버전을 설치하고, 다른 프로젝트와 격리시킴.
- **생성 방법**:
  ```bash
  python -m venv myenv

✅ venv를 쓰는 이유
| 문제 상황 | venv 사용 시 해결 방법 |
|-----------|-----------------------|
| 프로젝트 A는 `requests==2.6.0` 필요, 프로젝트 B는 `requests==3.0.0` 필요 | 각 프로젝트별 가상환경을 만들어 충돌 방지 |
| 운영체제 전체에 패키지를 설치하면 다른 프로그램에 영향 | venv는 **프로젝트 전용 환경**이므로 안전 |
| 협업 시 동일한 환경을 맞추기 어려움 | `requirements.txt`로 환경을 공유하면 누구나 같은 환경 재현 가능 |
| 테스트용으로 특정 버전의 라이브러리만 필요 | 가상환경을 쉽게 만들고 삭제할 수 있어 실험에 적합 |


✅ venv의 장점
- **격리성**: 다른 프로젝트와 독립적으로 패키지를 관리
- **재현성**: `requirements.txt`로 동일한 환경을 쉽게 복원
- **안전성**: 시스템 전체 파이썬 환경을 건드리지 않음
- **유연성**: 필요할 때마다 새로운 환경을 만들고 삭제 가능

---

🚨 주의할 점
- 프로젝트 코드와 가상환경을 섞지 말 것
- venv 디렉터리는 보통 `.gitignore`에 추가
- 환경 이름은 `.venv` 또는 `venv`를 많이 사용 (숨김 처리 및 툴 호환성 때문)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows (cmd/PowerShell)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

활성화되면 터미널 프롬프트 앞에 `(venv)`가 붙습니다.

### Step 4. 필수 패키지(라이브러리) 설치

프로젝트에 필요한 모든 외부 라이브러리들을 한 번에 설치합니다.

```bash
pip install -r requirements.txt
```

### Step 5. API 키 발급 및 `.env` 설정

1. https://platform.openai.com/api-keys 접속 후 로그인
2. "Create new secret key" 클릭 → 키 복사 (한 번만 보여주므로 안전한 곳에 저장)
3. 프로젝트 루트에 `.env` 파일 생성 (`.env.example`을 복사해서 사용)

```bash
# macOS / Linux
cp .env.example .env

# Windows
copy .env.example .env
```

4. `.env` 파일을 열어 아래처럼 실제 키로 교체

```
OPENAI_API_KEY=sk-proj-실제발급받은키
```

> ⚠️ `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 절대 올라가지 않습니다. 실수로 커밋하지 않도록 주의하세요.

### Step 6. 실행

```bash
python main.py
```

프롬프트가 뜨면 브리프 파일 경로(예: `brief.json`)를 입력하면 됩니다.

### 최종 폴더/설정 체크리스트

- [ ] Python 3.9+ 설치 완료
- [ ] `venv` 생성 및 활성화 (`(venv)` 표시 확인)
- [ ] `pip install -r requirements.txt` 완료
- [ ] `.env` 파일 생성 + API 키 입력 완료
- [ ] `python main.py` 실행 시 정상적으로 입력 프롬프트가 나타남

---

## 📌 Git 명령어 정리 

처음 Git 저장소를 만들고 GitHub에 올리는 과정을 순서대로 정리했습니다.

| 순서 | 명령어 | 설명 |
|---|---|---|
| 1 | `git init` | 현재 폴더를 Git 저장소로 초기화 |
| 2 | `git add .` | 모든 변경 파일을 커밋 대상(스테이징)에 추가 |
| 3 | `git commit -m "Initial commit"` | 스테이징된 변경사항을 커밋(저장) |
| 4 | `git remote add origin "https://github.com/사용자명/저장소명.git"` | GitHub 원격 저장소 주소 등록 (Windows에서는 따옴표 사용 권장) |
| 5 | `git branch -M main` | 기본 브랜치 이름을 `main`으로 설정 |
| 6 | `git push -u origin main` | 원격 저장소로 푸시 + 로컬-원격 브랜치 추적(tracking) 연결 |

### ⚠️ 처음 Git을 세팅할 때 자주 겪는 문제와 해결

| 문제 상황 | 원인 | 해결 방법 |
|---|---|---|
| `git remote add` 이후 `git push`만 하면 에러 발생 | `remote add`는 원격 주소만 등록할 뿐, 브랜치 추적(tracking)까지 자동으로 설정해주지 않음 | `git push -u origin main`처럼 `-u` 옵션을 반드시 사용 (또는 `git clone`으로 시작) |
| `fatal: refusing to merge unrelated histories` | GitHub에서 저장소 생성 시 README 등을 자동 생성해, 로컬과 원격의 커밋 历사가 서로 다름(diverged) | `git pull origin main --allow-unrelated-histories` 로 두 히스토리를 강제로 병합 |
| `<<<<<<<`, `=======`, `>>>>>>>` 마커가 파일에 남음 | 병합(merge) 과정에서 충돌(conflict)이 발생 | 충돌난 파일을 직접 열어 원하는 내용만 남기고 마커를 삭제한 뒤 `git add` → `git commit`으로 병합 완료 |
| Windows에서 줄바꿈(LF/CRLF) 경고 | Windows(CRLF)와 Git 표준(LF)의 줄바꿈 방식 차이 | 프로젝트 루트에 `.gitattributes` 파일을 추가해 `* text=auto`로 자동 정규화 설정 |

### 이후 변경사항을 올릴 때 (일상적인 흐름)

```bash
git add .
git commit -m "기능 설명 커밋 메시지"
git push
```

---

이 프로젝트를 완성하면 아래 내용들을 배울 수 있어요:

- ✅ **LLM API 사용법**: OpenAI/Claude 같은 AI로 텍스트 만들기

      OpenAI(ChatGPT)나 Anthropic(Claude) 같은 AI 서비스에 인터넷으로 질문을 보내고 답변을 받는 방법을 배웁니다.
      AI를 "웹사이트에서 채팅으로만" 쓰는 것과 "내 프로그램 안에서 자동으로 부르는 것"은 완전히 다릅니다. 후자를 할 수 있어야 진짜 AI 서비스를 만들 수 있어요!

   📝 이 프로젝트에서 배우는 부분

            from openai import OpenAI

            client = OpenAI(OPEN_AI_KEY)
            response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "브랜드 이름 3개 추천해줘"}]
            )
            print(response.choices[0].message.content)

- ✅ **이미지 생성 AI**: DALL-E, GPT-IMAGE-1로 이미지 만들고 저장하기

      텍스트 설명을 입력하면 그림을 그려주는 AI(DALL-E, GPT-IMAGE-1)를 사용하는 방법을 배웁니다.
      텍스트뿐만 아니라 이미지도 자동으로 생성할 수 있게 되면, 만들 수 있는 서비스의 폭이 훨씬 넓어져요. (썸네일 자동 생성, 로고 제작, 일러스트 등)

      📝 이 프로젝트에서 배우는 부분
      generators/logo.py에서 "친환경 화장품 브랜드의 미니멀한 로고" 같은 설명으로 로고 이미지 만들기
      생성된 이미지 URL을 다운로드해서 PNG 파일로 저장하기

            response = client.images.generate(
            model="gpt-image-1",
            prompt="자연주의 화장품 브랜드의 미니멀한 로고, 초록색 계열",
            size="1024x1024"
            )
            image_url = response.data[0].url  # 이미지 주소 받기


- ✅ **JSON 형태로 답변 받기**: AI가 정해진 형식으로 대답하게 만들기

      📝 이 프로젝트에서 배우는 부분
      OpenAI의 response_format={"type": "json_object"} 옵션 사용하기
      Pydantic으로 응답 형식이 올바른지 검사하기

            response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},  # ← JSON 형식 강제!
            messages=[...]
            )
            data = json.loads(response.choices[0].message.content)
            names = data["names"]  # 바로 사용 가능!

- ✅ **프롬프트 작성법**: 원하는 결과를 얻는 질문 만드는 법

      📝 이 프로젝트에서 배우는 부분
      prompts/ 폴더에서 각 생성 작업별 프롬프트 템플릿 만들기
      역할 부여, 조건 명시, 형식 지정, 예시 제공 기법 익히기

            당신은 브랜드 네이밍 전문가입니다.
            아래 조건에 맞는 브랜드 이름 5개를 제안해주세요.

            - 업종: 친환경 화장품
            - 타겟: 20~30대 여성
            - 톤: 따뜻하고 신뢰감 있는
            - 형식: JSON ({"names": [{"ko": "...", "en": "...", "meaning": "..."}]})


- ✅ **여러 작업 순서 관리**: 여러 API 호출을 차례대로 처리하기

      📝 이 프로젝트에서 배우는 부분
      main.py에서 각 생성기(generator)를 순서대로 호출하기
      이전 단계 결과를 다음 단계 입력으로 넘기기 (예: 이름 → 로고 프롬프트에 활용)

            def run_pipeline(brief):
            result = {"brief": brief, "errors": []}
            result["naming"] = generate_names(brief)
            result["slogans"] = generate_slogans(brief, result["naming"])
            result["story"] = generate_story(brief, result["naming"])
            result["palette"] = generate_palette(brief)
            result["logos"] = generate_logos(brief, result["naming"], result["palette"])
            return result



- ✅ **오류 대응**: 일부 실패해도 계속 진행되는 튼튼한 프로그램 만들기
      API 호출이 실패했을 때 프로그램이 죽지 않고, 다시 시도하거나 대체 방안을 실행하는 방법을 배웁니다.

      📝 이 프로젝트에서 배우는 부분
      try-except로 각 생성 단계 감싸기
      재시도 로직: 실패하면 잠시 기다렸다가 다시 시도 (최대 3회)
      부분 실패 허용: 로고 생성이 실패해도 이름/슬로건은 저장

            import time

            def call_with_retry(func, max_retries=3):
            for attempt in range(max_retries):
                  try:
                        return func()
                  except Exception as e:
                        if attempt == max_retries - 1:
                        raise
                        time.sleep(2 ** attempt)  # 2초, 4초, 8초 대기




- ✅ **API 키 안전하게 다루기**: 환경변수로 비밀 정보 관리하기

      📝 이 프로젝트에서 배우는 부분
      .env 파일에 API 키 저장하기
      python-dotenv로 불러오기
      .gitignore에 .env 추가해서 GitHub 업로드 방지

            # .env 파일
            OPENAI_API_KEY=sk-proj-xxxxx

            # 파이썬 코드
            from dotenv import load_dotenv
            import os

            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")  # 안전하게 불러오기


- ✅ **색상 시각화**: matplotlib으로 색상 팔레트 그리기
      AI가 알려준 색상 코드(예: #5D7B6F)를 실제 눈으로 볼 수 있는 이미지(PNG)로 만드는 방법을 배웁니다. 
      "main": "#5D7B6F"라는 텍스트만 봐서는 어떤 색인지 몰라요. 팔레트 이미지로 만들어야 클라이언트가 "아, 이런 느낌이구나!" 하고 이해할 수 있죠.

      📝 이 프로젝트에서 배우는 부분
      matplotlib으로 색상 사각형 그리기
      HEX 코드(#5D7B6F)를 색상으로 변환하기
      PNG 파일로 저장하기

            import matplotlib.pyplot as plt

            colors = ["#5D7B6F", "#E8DFCA", "#A8B5A0"]
            fig, ax = plt.subplots(figsize=(len(colors) * 2, 3))
            for i, color in enumerate(colors):
            ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=color))
            ax.set_xlim(0, len(colors))
            plt.savefig("output/palette.png")




- ✅ **CLI 만들기**: 명령어로 실행하는 프로그램 설계

            python main.py --input brief.json --output ./output

      이렇게 명령어 하나로 실행되는 도구는 파이썬 표준 라이브러리인 **argparse**를 사용합니다

            import argparse

            parser = argparse.ArgumentParser(description="브랜드 아이덴티티 생성기")
            parser.add_argument("--brief", required=True, help="입력 브리프 JSON 파일 경로")
            parser.add_argument("--output", default="output", help="결과물 저장 폴더")
            parser.add_argument("--with-competitor", action="store_true", help="경쟁사 분석 포함")

            args = parser.parse_args()
            print(args.brief)  # 사용자가 입력한 값 사용

      💻 우리 프로젝트에서 어떻게 쓰이나요?
      main.py의 CLI 구조를 다시 볼까요?

      #### 최소 실행 (필수 옵션만)
      python main.py --brief brief_example.json

      #### 결과 폴더 지정
      python main.py --brief brief_example.json --output my_brands/

      #### 경쟁사 분석까지 포함 (보너스 기능 ON)
      python main.py --brief brief_example.json --with-competitor

      #### 도움말 보기
      python main.py --help


🔍 실행 시 내부 흐름

사용자 입력 (터미널)
    ↓
argparse가 옵션 파싱
    ↓
--brief 파일 읽기 → validator로 검증
    ↓
각 generator 순차 실행 (naming → slogan → story → palette → logo)
    ↓
--with-competitor 있으면 경쟁사 분석 추가
    ↓
--output 폴더에 결과 저장
    ↓
최종 리포트 출력 (종료 코드 0)



## 📌 Git이란?

Git은 소스 코드의 변경 이력을 관리하는 **분산 버전 관리 시스템(DVCS, Distributed Version Control System)**이다.
파일이 어떻게 변경되어 왔는지를 시간 순서대로 기록하고, 필요하면 과거 특정 시점으로 되돌리거나 여러 사람이 동시에 작업한 내용을 하나로 합칠 수 있게 해준다.

### Git의 핵심 특징

- **분산 구조**: 중앙 서버(예: GitHub)뿐 아니라 개발자 각자의 로컬 컴퓨터에도 전체 저장소(히스토리 포함)의 복사본이 존재한다. 서버가 다운되어도 로컬에서 작업을 계속할 수 있다.
- **스냅샷 기반 저장**: 파일의 "변경분(diff)"만 저장하는 다른 시스템과 달리, Git은 커밋할 때마다 전체 프로젝트 상태를 스냅샷으로 저장한다. (내부적으로는 중복을 제거해 효율적으로 저장)
- **빠르고 가벼운 브랜치**: 브랜치 생성/전환 비용이 매우 낮아 새로운 기능이나 실험을 부담 없이 시도할 수 있다.
- **무결성 보장**: 모든 커밋은 SHA-1 해시로 식별되어, 파일이나 히스토리가 변조되면 즉시 감지할 수 있다.
- **비선형 개발 지원**: 여러 브랜치에서 동시에 작업하고 나중에 병합(merge)하는 방식의 개발이 가능하다.

### Git이 왜 필요한가

1. **변경 이력 관리**: "언제, 누가, 무엇을, 왜" 변경했는지 커밋 메시지와 함께 기록되므로 문제가 생겼을 때 원인 추적이 쉽다.
2. **협업 지원**: 여러 명이 같은 프로젝트를 동시에 작업해도 각자의 변경 사항을 브랜치로 분리했다가 병합할 수 있어 충돌을 최소화한다.
3. **백업 및 복구**: 실수로 코드를 삭제하거나 잘못 수정해도 이전 커밋으로 되돌릴 수 있다.
4. **실험적 개발 가능**: 새로운 기능을 메인 코드에 영향을 주지 않고 별도 브랜치에서 자유롭게 시도해볼 수 있다.
5. **코드 리뷰 및 품질 관리**: GitHub 등과 연동하면 Pull Request를 통해 다른 사람의 코드를 리뷰하고 병합 전에 품질을 검증할 수 있다.
6. **원격 협업**: GitHub, GitLab 같은 원격 저장소를 통해 지리적으로 떨어진 팀원들과도 코드를 공유하고 동기화(push/pull)할 수 있다.

### Git이 없다면?

- 파일을 `최종.py`, `최종_진짜.py`, `최종_진짜_수정.py` 처럼 수동으로 버전 관리해야 한다.
- 여러 명이 같은 파일을 수정하면 서로의 작업을 덮어쓸 위험이 크다.
- 특정 시점의 코드로 되돌리기 어렵고, 무엇이 왜 바뀌었는지 알기 힘들다.



## 📌 API 키 설정 방법

- 프로젝트 루트 경로에 .env 파일을 생성하고 아래와 같이 작성합니다.

       OPENAI_API_KEY=your_openai_api_key  

- 각 키의 용도
  
       OPENAI_API_KEY : 브랜드 브리프 텍스트 생성 및 로고 이미지 생성
    
**✅ 환경변수 관리 이유**
     
       API 키를 소스코드에 직접 작성하면 GitHub 업로드, 화면 공유, 코드 제출 과정에서 쉽게 유출될 수 있습니다.
       따라서 환경변수 또는 .env 파일로 분리하여 관리하는 것이 안전합니다.  
    
🔹 보안: API 키를 코드에 직접 작성하면 깃허브 등 공개 저장소에 유출될 위험이 있음  
🔹 유연성: 개발/운영 환경마다 다른 키를 쉽게 적용 가능  
🔹 재사용성: 여러 프로젝트에서 동일한 키를 공유할 때 편리  

🔹 원칙: .env 파일 → dotenv 라이브러리 → os.getenv()로 불러오기   

*API 키는 매우 중요한 민감정보이므로 아래 사항을 반드시 지켜야 합니다.*

🔹주의사항
   - API 키를 코드에 직접 작성하지 않는다.
   - .env 파일은 GitHub에 업로드하지 않는다.
   - .gitignore에 .env를 반드시 포함한다.
   - 화면 캡처, 발표 자료, 제출 문서에 키가 보이지 않도록 주의한다.
   - 키가 노출되었다면 즉시 폐기하고 새 키를 발급받는다. 


## 📌 에러 처리 가이드

*API 호출 시 발생할 수 있는 오류 상황과 대응 방법*에 해당하는 내용을 정리한 표입니다.
이 프로그램은 **한 단계가 실패해도 전체가 멈추지 않고, 실패한 단계만 건너뛰고 계속 진행**하는 것을
기본 원칙으로 합니다.

| 오류 상황 | 발생 원인 | 프로그램의 대응 | 사용자가 해야 할 일 |
|---|---|---|---|
| **API 키 누락** (`OPENAI_API_KEY` 없음) | `.env` 파일을 만들지 않았거나 환경변수 미설정 | 프로그램 시작 직후 감지하여 안내 메시지 출력 후 **즉시 종료** (`sys.exit(1)`) | `.env` 파일에 `OPENAI_API_KEY=sk-...` 추가 |
| **API 키 인증 실패** (`AuthenticationError`) | 키 값이 잘못되었거나 만료/폐기됨 | 해당 단계(네이밍/슬로건/스토리/컬러/로고)에서 에러 메시지 출력 후 **해당 단계만 건너뛰고 다음 단계 진행** | OpenAI 대시보드에서 키 상태 확인, 새 키 발급 후 `.env` 갱신 |
| **API 요청 한도 초과** (`RateLimitError`) | 짧은 시간에 너무 많은 요청을 보냈거나 사용량 한도 초과 | 에러 메시지 출력 후 해당 단계를 건너뛰고 계속 진행 | 잠시 후 재실행, 또는 OpenAI 요금제/한도 확인 |
| **네트워크 연결 오류** (`APIConnectionError`) | 인터넷 연결 불안정, 방화벽/프록시 차단 | 에러 메시지 출력 후 해당 단계를 건너뛰고 계속 진행 | 네트워크 상태 확인 후 재실행 |
| **OpenAI 서버 오류** (`APIError`, 5xx 등) | OpenAI 서비스 자체의 일시적 장애 | 에러 메시지 출력 후 해당 단계를 건너뛰고 계속 진행 | 잠시 후 재시도, [OpenAI 상태 페이지](https://status.openai.com) 확인 |
| **JSON 파싱 실패** (`JSONDecodeError`) | LLM 응답이 JSON 형식이 아니거나 형식이 깨짐 | 에러 메시지 출력 후 해당 단계 결과를 빈 값으로 처리, 다음 단계 진행 | 재실행 시 대부분 정상 생성됨 (모델 응답 변동성) |
| **브리프 파일 없음/경로 오류** | 사용자가 잘못된 경로 입력 | `[브리프 오류]` 메시지 출력 후 프로그램 종료 | 올바른 파일 경로 재입력 |
| **브리프 JSON 형식 오류** | JSON 문법 오류(콤마 누락 등) | 오류 위치와 함께 메시지 출력 후 프로그램 종료 | JSON 문법 검사 후 재실행 (예: [jsonlint.com](https://jsonlint.com)) |
| **브리프 필수 필드 누락** | `industry`/`target`/`keywords` 중 하나라도 없음 | 누락된 필드명을 출력하고 프로그램 종료 | 브리프 파일에 필수 필드 추가 후 재실행 |
| **로고 이미지 저장 실패** (디스크/권한 문제) | 출력 폴더 쓰기 권한 없음, 디스크 용량 부족 등 | 에러 메시지 출력 후 해당 로고만 건너뛰고 다음 로고 계속 생성 | 출력 폴더 권한/용량 확인 |

✅ 오류 화면  

|API KEY 설정 오류| 이미지 생성 모델(dall-e)오류|입력파일 오류|
|---|---|---|
|<img width="812" height="391" alt="image" src="https://github.com/user-attachments/assets/9c47fd7a-7b03-4f45-a7c8-5759b0861c5a" />|<img width="1612" height="789" alt="image" src="https://github.com/user-attachments/assets/9cd7bc68-dd2a-4902-b590-13ed8113c2c2" />|<img width="613" height="179" alt="image" src="https://github.com/user-attachments/assets/7c523e07-51d7-4e34-8f08-a37d9bcd20f9" />|

> 설계 원칙: 텍스트 생성과 이미지 생성은 서로 독립적으로 동작하도록 만들어,
> 예를 들어 로고 생성에 실패하더라도 이미 만들어진 네이밍/슬로건/스토리/컬러 결과는
> 정상적으로 `result.json`에 저장됩니다.


✅ 정상 실행 화면  

| 입력 파일(json) |정상 실행 스크린샷| 결과 파일저장 스크린샷|
|---|---|---|
|<img width="300" height="198" alt="image" src="https://github.com/user-attachments/assets/cfef4d20-86cc-4196-8373-ea8fbdf041c2" />|<img width="600" height="660" alt="image" src="https://github.com/user-attachments/assets/a982952b-a745-411a-9dd8-b36d4d7cb68a" /><br><img width="600" height="422" alt="image" src="https://github.com/user-attachments/assets/a0d45e36-c070-4965-a370-44f0e1fc1810" />|<img width="300" height="215" alt="image" src="https://github.com/user-attachments/assets/5f745602-a1c4-4385-8a26-be1c7c6584a0" />
|