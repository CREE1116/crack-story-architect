---
name: crack-story-architect
description: Design, compile, or audit production-grade Crack interactive story chats from story.md and characters.md into platform-limited prompts and keyword books. Use for worldbuilding, psychologically generative characters, player agency, pacing, combat loops, adult boundaries, prompt compression, cinematic openings, and Crack showcase sites, image hosting, banners, and onboarding descriptions.
---

# 크랙 스토리챗 아키텍트 (Crack Story Architect)

두 저작 원본 `story.md`·`characters.md`로부터 플랫폼 규격(7K/1K/400자)에 맞춘 **프로덕션급 인터랙티브 스토리챗과 키워드북**을 설계·컴파일한다.

---

## 🚀 선택형 설계 단계 + 3단계 제작 파이프라인

> [!IMPORTANT]
> **구상 설계 → 정본 작성 → 플랫폼용 컴파일을 분리합니다.** 사용자가 아이디어·세계관·인물을 함께 구상하거나 수정하고 싶다면 먼저 Phase 0에서 설계합니다. 이 단계에서 `build/` 파일을 만들거나 플랫폼 한도에 맞춰 생각을 줄이지 않습니다. 구상이 이미 확정되어 있으면 Phase 0을 건너뜁니다.

```text
[Phase 0. 구상 설계 (선택)]       대화·비공식 설계 메모 (플랫폼 규격 없음)
       ↓ 세계관 설계·수정·개선, 이야기·인물, 나레이터 톤 탐색; 확정/제안/미정 구분
[Phase 1. 정본 작성 (Authoring)]  story.md + characters.md  (글자 수 제한 없음)
       ↓ 합의된 설계를 정본화: 인물의 선택 근거, 세계 법칙, 갈등과 사건 조건
[Phase 2. 프롬프트 컴파일 (Compiling)] build/* + start-sets/* (7K / 1K / 400자 엄수)
       ↓ 전보체 명부 기호학, 3단 파싱, 샌드위치 하네스, 2대 키워드북, 다중 시작 세트
[Phase 3. 파생 에셋 생성 (Derived Assets)] build/assets/*   (크랙 웹 등록 및 온보딩)
         단부루 태그 위키 검증 프롬프트 시트, 상세설명(배너·자산표·단축어), 고정 댓글(명부·이미지 코드·상태창 범례), Pages 배포
```

---

## 🧭 진입 즉시 적용할 8대 핵심 기준

1. **원작 창작과 프롬프트 컴파일의 철저한 분리**:
   - `story.md`와 `characters.md`는 인물의 심리적 모순과 세계의 물리적 법칙을 구축하는 **글자 수 무제한의 정본(Canon)**이다.
   - `build/`는 이를 7,000자 / 1,000자 / 400자 규격에 맞춰 기계 실행용으로 압축 컴파일한 **사본 및 파생물**이다.
2. **인물 설계 점검 틀 (3개 층위 & 8칸)**:
   - 세계의 사실 ➔ 인물의 해석·욕구 ➔ 관찰 가능한 행동을 구분해 인과를 점검한다. 이 저장소의 8칸·10단계는 검증된 인지 모형이 아닌 창작 도구다.
   - 충돌 욕구·취약점·느린 변화는 작품에 필요한 인물에게만 설계한다. 모든 인물에게 트라우마나 정해진 회복 단계를 강제하지 않는다.
3. **GREED식 단일 상태창 하네스 (Info 작업 기억 루프)**:
   - 매 턴 최하단 ```Info``` 상태창(시각·위치·성장·소지·인물관계·목표·상황)으로 작업 기억을 갱신한다.
   - LLM의 내부 상태 장부가 없으므로, 직전 턴에 출력한 Info 상태창이 다음 턴의 유일한 **작업 기억(Working Memory)**이다.
4. **3단 입력 파싱 규약 & OOC**:
   - `[지시: 내용]`(메타 연출/속도 조율)은 대사화하지 않고 연출 지침으로 즉각 반영한다.
   - `*행동 지문*`과 `"대사"`를 명확히 분리하며, `/OOC` 입력 시 역할극을 멈추고 설정/사실을 중립적으로 안내한다.
5. **PC 주권 & 안티메리수**:
   - {user}의 모든 대사, 속마음(`💭`), 행동, 감정, 결정을 AI가 대신 연기·대필·임의조작하는 것을 엄격히 금지한다.
   - 유저 발화를 나레이터 지문에서 직접 복붙하지 않고 간접 서술로 전환하며, 이유 없는 숭배(메리수)를 차단한다.
6. **전보체 인물 명부 (Telegraphic Roster — GREED 표준)**:
   - `▶이름｜나이·신분｜외형·무장｜MBTI｜戀慾｜望｜화법｜「능력」` 형식으로 압축한다.
   - 인물의 핵심 욕망(`望`), 인정 잣대(`認`), 연애/성애 적극성(`戀/慾`) 3대 축으로 NPC 보이스 평준화(Same-face)를 원천 차단한다.
7. **다중 시작 세트(2~3 루트) & 키워드북 2대 축**:
   - 단일 시작 강제를 탈피하여 2~3개의 다중 시작 세트(`01_default`, `02_alternate`, `03_crisis`)를 표준으로 구성한다.
   - 키워드북은 **[설정 압축형]**(인물/지리)과 **[문체 조절형]**(전투/스킨십 톤)으로 분리하며, `.` 상시 트리거 핵을 배제한다.
8. **크랙 파생 에셋 폴더(`build/assets/`) 및 정보 한도 준수** (키워드북은 SAFE·UNSAFE 각각 **20항목 상한**, 떡밥 단계의 발동 조건은 그보다 먼저 켜지는 곳에):
   - 상세설명(마크다운: 배너·사이트 링크·이미지 자산 표·단축어)과 첫 고정 댓글(평문: 식별번호 명부·이미지 출력 양식과 코드·상태창 범례)을 엄격히 분리한다. 상세설명에 세계관 설명을 쓰지 않고, 제작자 코멘트는 작성자가 쓴다.
   - 비밀·트라우마 스포일러를 차단하고 Day 1 유저 정보 한도 안에서 4대 플레이 팁(동료/탐색/자원/자유도)으로 치환한다.
   - `tools/images/search_tag.py` 단부루 위키를 검색해 검증된 공식 태그로 비주얼 에셋 시트를 완성한다.

---

## 🗺️ 핵심 모듈 라우팅 맵

작업하려는 단계의 모듈을 열고, 연결된 제작·배포가 필요할 때 관련 모듈을 추가로 읽는다. 링크는 스킬 기준 디렉터리(`${CLAUDE_PLUGIN_ROOT}`) 안의 경로다. 여러 문서를 오갈 필요 없이 각 모듈 안에서 원리·템플릿·체크리스트가 완결된다.

| 단계 | 작업 내용 | 열람할 모듈 | 모듈에 담긴 핵심 지식 |
|:---:|---|---|---|
| **Phase 0 (선택)** | **세계관 설계·수정·개선** | [worldbuilding-methods.md](references/worldbuilding-methods.md) | 핵심 전제에서 사회·일상·세력을 파생, 설정 변경의 연쇄 영향 추적, 문제별 개선, 정본으로 넘길 결정 구분 |
| **Phase 0 (선택)** | **이야기·캐릭터 기획** | [creative-methods.md](references/creative-methods.md) | 짧은 구상에서 갈등·관계·인물 방향 탐색, 장면 실험, 정본 이전의 창작 대화 |
| **Phase 0 (선택)** | **나레이터 톤·문체 설계** | [narrator-tone-design.md](references/narrator-tone-design.md) | 나레이터의 위치·지식·태도·침묵·유머, 같은 사건의 목소리 시안 비교, 장면별 일관성 |
| **Phase 0 (근거 확인)** | **설계 방법론의 연구 근거·한계** | [design-evidence.md](references/design-evidence.md) | 원 연구의 관찰·창작 설계 추론·미검증 가설 구분, FSA의 검증 범위와 비교 실험 |
| **Phase 1** | **스토리·인물 정본 작성** | [authoring-story-and-characters.md](references/authoring-story-and-characters.md) | 사실·인물 해석·행동 구분, 선택형 8칸·10개 질문, 변화의 근거, 세계 규칙과 사건 조건, 정본 작성법 |
| **Phase 2** | **올인원 마스터 프롬프트 컴파일** | [master-prompt-template.md](references/master-prompt-template.md) | GREED 규격 백지 마스터 템플릿(Clean Canvas), 3단 파싱, Info 상태창 하네스, 전보체 명부 기호학, 실전 GREED 헌터 레이드 완성본 |
| **Phase 2** | **키워드북 컴파일 / 슬롯 관리** | [keyword-book-guide.md](references/keyword-book-guide.md) | 설정 압축형 + 문체 조절형 템플릿, 부분문자열 충돌 방지, 1~5개 키워드 룰, 3슬롯 예산 관리, `.` 핵 배제 |
| **Phase 2** | **서사 속도 / NPC 능동성 / PC 주권** | [narrative-and-agency.md](references/narrative-and-agency.md) | PC 주권, 간접 인용, 비피학적 현실저항 가드, 발화자 1~3명 상한, 시간 Desync 방어, HUD 작업 기억 루프 |
| **Phase 2** | **다중 시작 세트 / 프롤로그 / 오프닝** | [openings-and-start-sets.md](references/openings-and-start-sets.md) | 다중 시작 세트(2~3개 루트) 표준 규약, 7단 줌인 프롤로그, 4단 핫스타트 오프닝, 세트별 추천 답변 3종 결속 |
| **Phase 3** | **크랙 파생 에셋 / 쇼케이스 / 플레이 팁** | [derived-assets-and-showcase.md](references/derived-assets-and-showcase.md) | `build/assets/` 산출물 규약, 상세설명(배너·자산표·단축어), 고정 댓글(식별번호·이미지 양식/코드·상태창 범례), 30자 후크, 4대 플레이 팁 치환 |
| **Phase 3** | **단부루 태그 위키 / 캐릭터·배경 CG** | [image-prompt-and-assets.md](references/image-prompt-and-assets.md) | `search_tag.py`(태그 검색), `compose_scene.py`(배경 컴파일), `crop_backgrounds.py`(1024x400 크롭), `name_card_cinematic.py`(시네마틱 명함), 태그 가감 원칙, **이미지 코드 규약(s00/s01~/a01~/bg)·압축 출력 규칙·명함 이름 노출·프롤로그 이미지 배치** |
| **Phase 3** | **캐릭터 외형 디자인 / `characters.json`** | [character-visual-design.md](references/character-visual-design.md) | 캐스트 표·세력 룩(공통 표식 vs 개인 욕망), 세계 공통 팔레트·60-30-10, 단부루 검증 헤어·눈매·체형 태그 카탈로그, 미형 가드, 오해 조합, 300~450자·가중치 2곳·자연어 1문장 `.,` 컴파일 규칙, UC 6단, 정본 동기화 |
| **Phase 3** | **작품 연장형 사이트 설계 / 공개 정보 경계** | [immersive-showcase-design.md](references/immersive-showcase-design.md) | 네 참고 사이트 기반 프리셋, 기록자·시점·열람 권한, 관측·소문·비밀 분리, 사이트에서 플레이로 이어지는 설계 양식, HTML/CSS 템플릿 3종 |
| **Phase 3** | **이미지 호스팅 / 소개 사이트 / 배너** | [hosting-showcase-and-banner.md](references/hosting-showcase-and-banner.md) | 공개 파일 계약, `pages_bundle.py`(코드명 번들·Pages 배포·HEAD 전수 검증·404 함정), `make_cover.py`·`glitch.py`(표지·배너), 배너 제목·구도 |
| **Phase 3** | **크랙 스튜디오 입력·임시저장** | [tools/sync/README.md](tools/sync/README.md) | `crack_sync.py` 헤드리스 자동 주입, storyId 재주입, 표지 지정, 제목 접미사·20항목 상한 등 함정 |
| **Common** | **플랫폼 규격 / 글자 수 / 단축어 / 검증** | [platform-spec-and-lint.md](references/platform-spec-and-lint.md) | 7K/1K/400자 규격, UTF-16 측정법, 비가시적 조향 주석, 단축어 6대 표준 레시피, 빌드 체크리스트 |
| **Common** | **단축어 설계 / 예시 변환** | [shortcut-authoring.md](references/shortcut-authoring.md) | 호출·RP 중단/재개·출력 형식·기억 경계·PC 주권 계약, 요약/OOC/스킵/SNS/엔딩 유형별 설계와 400자 압축 |

### 설계와 제작의 경계

Phase 0의 방법론은 **필요할 때만** 읽는다. 학술 연구를 근거로 제시할 때는 [근거 지도](references/design-evidence.md)에서 원 연구의 관찰과 창작용 추론을 구분한다. 사용자가 세계관이나 인물을 설계·수정하라고 한 작업을 곧바로 프롬프트 제작 요청으로 해석하지 않는다. 설계에서 확정된 사실만 Phase 1의 `story.md`·`characters.md`로 옮기고, 그 정본만 Phase 2·3의 제작 입력으로 쓴다. 미정·대안·실험 장면을 확정 설정이나 새 필수 슬롯으로 취급하지 않는다.

---

## 📦 프로젝트 표준 디렉토리 및 산출물 체계

```text
<project>/
├── story.md                       # [Phase 1 정본] 세계관 물리 법칙, 갈등 엔진, 서사 아크 (무제한)
├── characters.md                  # [Phase 1 정본] 8대 심리 슬롯, 충돌 욕구, 역린, 연대기 앵커 (무제한)
├── start-sets/                    # [Phase 2 표준] 다중 시작 세트 (루트별 파일 완전 결속)
│   ├── 01_default/                # 정규 / 입문 루트 (default: true)
│   │   ├── meta.md                # 제목, 설명, 순서 (order: 0)
│   │   ├── prologue.md            # 7단 줌인 도입 원고 (≤ 1,000자)
│   │   ├── start-prompt.md        # 4단 핫스타트 첫 턴 상황 압박 (≤ 1,000자)
│   │   └── recommended-replies.md # 세트 전용 추천 첫 답변 3개 (--- 구분)
│   ├── 02_alternate/              # 대안 / 전략 루트
│   │   └── meta.md, prologue.md, start-prompt.md, recommended-replies.md
│   └── 03_crisis/                 # 위기 / 하드코어 루트 (선택적)
└── build/                         # [Phase 2 & 3 컴파일 생성물]
    ├── integrated-prompt-safe.md  # 전연령 통합 시스템 프롬프트 (≤ 7,000자)
    ├── integrated-prompt-unsafe.md# 19+ 성인 통합 시스템 프롬프트 (≤ 7,000자)
    ├── keyword-book*.md           # 키워드북 등록표 (항목당 ≤ 400자)
    ├── prologue.md                # 기본 시작 세트 사본 (≤ 1,000자, 단일 세트 뷰어 호환)
    ├── start-prompt.md            # 기본 시작 세트 사본 (≤ 1,000자, 단일 세트 뷰어 호환)
    └── assets/                    # 🌟 [Phase 3 파생 에셋 공식 디렉토리]
        ├── story-description.md   # 크랙 상세설명란 (마크다운: 배너·사이트 링크·이미지 자산 표·단축어)
        ├── summary-comment.md     # 크랙 첫 고정 댓글 (평문: 식별번호 명부·이미지 양식/코드·상태창 범례·시작 팁)
        ├── play-guide.md          # 크랙 [시작 설정] 탭 플레이어 안내문
        ├── recommended-replies.md # 세트 공통 첫 추천 답변 3종 (--- 구분)
        ├── build-stamp.json       # 컴파일 시점 소스 해시 기록
        ├── characters.json        # NAI 가중치 베이스 프롬프트 + UC JSON (GREED 표준)
        ├── image-prompts.md       # 단부루 검증 공식 태그 기반 일러스트 프롬프트 시트
        ├── prompts.json           # 기계 판독용 이미지 프롬프트 JSON
        ├── character-design.md    # 인물 시각 디자인 명세표
        └── scene-design.md        # 배경 및 장면 시각 디자인 명세표
```

---

## ✅ 컴파일 후 필수 검증 (Validation Gate)

규격 위반은 플레이 중에 아무 신호도 내지 않는다. 프롬프트만 조용히 잘리고, 모델만 조용히 옛 설정을 연기한다.
**Phase 2 또는 Phase 3 산출물을 고쳤으면 반드시 검사기를 돌린 뒤에 완료를 보고한다.**

```bash
S="${CLAUDE_PLUGIN_ROOT:-.}"          # 플러그인 설치 경로. 레포에서 직접 쓰면 레포 루트.

"$S"/scripts/validate.sh <project>                  # 전체 검사
"$S"/scripts/validate.sh <project> --allow-unbuilt  # 아직 컴파일 전인 프로젝트
python3 "$S"/scripts/checks/check_freshness.py <project> --stamp   # 컴파일 직후 기준점 기록
```

> [!NOTE]
> `<project>`는 유저의 작업 디렉터리에 있는 스토리챗 프로젝트 경로다. 검사기는 플러그인 쪽에,
> 검사 대상은 유저 쪽에 있으므로 두 경로를 섞지 않는다. `validate.sh`는 자기 위치에서 레포 루트를
> 스스로 찾으므로 어디서 호출해도 동작한다.

| 검사기 | 잡는 것 |
|---|---|
| `check_freshness.py` | 원본을 고치고 재컴파일을 잊은 상태. 바뀐 섹션 → 다시 볼 산출물까지 지목 |
| `check_project_layout.py` | 정본 2개 / `build/` 산출물 6개 규약 |
| `check_build.py` | 7K·1K 한도, SAFE↔UNSAFE 섹션 제목 일치, 우회 문구 혼입 |
| `check_keyword_book.py` | 항목당 UTF-16 400자, 키워드 1~5개, **항목 수 20개 상한**, `.` 상시 트리거 핵, 단축어 슬래시·한도, 도달 불가 키워드(WARN) |
| `check_image_urls.py` | 프롤로그·시작 상황·상세설명·댓글의 이미지 URL 이 `image-codes.json` 배포 목록에 있는지 |
| `check_symbols.py` | 정의 없이 쓰인 기호·이모지, 범례보다 먼저 등장한 기호 |
| `check_character_prompts.py` | `characters.json` 키·길이·가중치 짝·자연어 `.,`·표정/배경/숫자 혼입·prompt↔uc 충돌·헤어 묶음 중복 |
| `check_image_assets.py` | 명부↔이미지 슬러그 불일치, 시드 중복, 선두 태그 충돌 |
| `check_showcase.py` | 공개정보 장부 필수값, 역할·시작 장소·상황·첫 행동, 사이트↔정본/시작세트 신선도 |
| `check_naming.py` | 폐기된 `char.` / `canon.` 점 표기 잔존 |

> [!IMPORTANT]
> `build/`에는 위 6개 산출물과 `assets/` 외의 파일을 두지 않는다. 중간 메모나 초안을 남기면 구조 검사가 실패한다.
> 기호를 새로 도입하면 `# 표기` 범례에 먼저 정의한다. 범례보다 먼저 등장한 기호는 실패로 잡힌다.

## 🧭 작업 시작 시 참조할 실물

아래 경로는 모두 **스킬 기준 디렉터리**(`${CLAUDE_PLUGIN_ROOT}`, 위 안내의 `$S`) 기준이다.
유저의 프로젝트 디렉터리가 아니다.

| 목적 | 경로 |
|---|---|
| 새 프로젝트 빈 양식 | `$S/templates/story-chat-template/` |
| `build/` 산출물 규약 | `$S/templates/build-dir-contract.md` |
| `build/assets/` 규약 | `$S/templates/build-assets-contract.md` |
| **완성된 참조 프로젝트** | `$S/examples/apocalypse/` — 정본부터 통합 프롬프트·키워드북·파생 에셋까지 전부 채워져 있고 CI가 검증한다 |
| 바로 사용하는 사이트 템플릿 | `$S/templates/showcase-sites/` — 전술 단말기·길드 게시판·기록관 HTML/CSS 및 디자인 지침 |
| 이미지 툴체인 | `$S/tools/images/` (Pages 번들: `pages_bundle.py`, 표지·배너: `make_cover.py`) |
| 크랙 자동 입력 | `$S/tools/sync/crack_sync.py` |
| 레퍼런스 | `$S/references/` |

새 프로젝트는 빈 양식을 유저 작업 디렉터리로 복사해서 시작한다:

```bash
cp -r "$S"/templates/story-chat-template <유저가 지정한 경로>
```

빈 양식만 보고 감이 오지 않으면 `$S/examples/apocalypse/`의 같은 파일을 먼저 읽는다.
