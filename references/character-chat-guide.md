# 캐릭터챗 아키텍처 및 제작 가이드 (Character Chat Guide)

크랙(Crack)의 **캐릭터챗**은 방대한 세계관과 사건 전개 중심의 스토리챗과 달리, **특정 캐릭터 1명과 1:1로 직접 마주 보고 실시간 채팅(대화)하는 감각**에 특화된 인터랙티브 챗입니다.

기본적으로 완성된 스토리챗(`story.md`, `characters.md`)의 세계관과 인물 정본에서 캐릭터를 추출(스핀오프)하여 생성하며, 스토리챗 프로젝트 내부의 `char_chat/<캐릭터이름>/` 디렉터리에 상주합니다.

---

## 1. 스토리챗 vs 캐릭터챗 플랫폼 규격

| 항목 | 캐릭터챗 규격 | 설명 및 역할 |
|---|---|---|
| **캐릭터 이름** | **≤ 30자** | 프로필 및 메신저에 노출되는 이름 |
| **한줄소개** | **≤ 30자** | 카드 노출용 로그라인 (예: "관리국 중사 서린과의 1:1 대화") |
| **시스템 프롬프트** | **≤ 2,000자** | 인물의 페르소나, 말투(Tone & Voice), 유저와의 1:1 관계성, 행동 원칙 |
| **플레이가이드** | **≤ 500자** | 유저를 위한 대화 시작 팁 (추천 화제, 캐릭터의 경계를 푸는 힌트) |
| **캐릭터 설명** | **≤ 1,000자** | 캐릭터 상세 프로필 및 매력적인 시놉시스 소개글 |
| **인트로 대화** | **각 발화 ≤ 150자** | 첫 입장 시 오프닝 핑퐁 (유저 발화 1세트 + 캐릭터 응답 1세트) |
| **예시 대화** | **각 발화 ≤ 150자, 최대 10개** | 캐릭터 특유의 말투와 반응 호흡을 학습시키는 Few-shot 대화 세트 |
| **시각 에셋** | **썸네일 / 상황 이미지** | 대표 프로필 사진 + 채팅방 배경/상황 일러스트 |
| **메타데이터** | **장르, 타겟, 해시태그** | (공개여부는 크랙 에디터 기본값 사용) |

---

## 2. 캐릭터챗 디렉터리 구조 (`char_chat/<캐릭터이름>/`)

스토리챗 프로젝트 내 `char_chat/` 폴더 아래에 캐릭터별 독립 디렉터리로 위치합니다.

```text
<story-project>/
├── story.md
├── characters.md
├── build/                           # 스토리챗 빌드 산출물
└── char_chat/                       # 🌟 [캐릭터챗 컬렉션]
    └── <캐릭터이름>/                 # 예: char_chat/서린/
        ├── character.md             # 캐릭터 정본 발췌 (페르소나, 심리, 대사 패턴)
        ├── dialogues.md             # 인트로 및 예시대화 마크다운 (수정 편집용)
        ├── guide.md                 # 플레이가이드 & 캐릭터 설명 마크다운
        ├── meta.yaml                # 이름, 한줄소개, 장르, 타겟, 해시태그
        ├── assets/                  # 썸네일(thumbnail.webp) 및 상황이미지(situation.webp)
        └── build/                   # [Playwright 주입용 정본 컴파일 산출물]
            ├── prompt.md            # ≤ 2,000자 시스템 프롬프트
            ├── play-guide.md        # ≤ 500자 플레이가이드
            ├── character-desc.md    # ≤ 1,000자 캐릭터 설명
            ├── intro.json           # 인트로 대화 JSON (유저 ≤150자, 캐릭터 ≤150자)
            ├── examples.json        # 예시대화 JSON 배열 (최대 10개)
            └── meta.json            # 기계 판독용 메타 JSON
```

---

## 3. 제작 및 추출 워크플로우

### 1단계: 스토리에서 캐릭터챗 자동 추출
스토리 정본(`story.md`, `characters.md`)에서 특정 캐릭터를 분석하여 `char_chat/<캐릭터이름>/` 디렉터리에 프로젝트 뼈대와 빌드 산출물을 즉시 생성합니다:

```bash
python3 scripts/derive_character_chat.py <스토리_경로> "<캐릭터이름>"

# 예시:
python3 scripts/derive_character_chat.py examples/apocalypse "서린"
# ➔ examples/apocalypse/char_chat/서린/ 생성 완료
```

### 2단계: 대화 및 페르소나 미세조정
- `char_chat/<캐릭터이름>/dialogues.md`: 1:1 대화의 맛을 살려 인트로 및 예시대화(1~10개)를 다듬습니다. (각 발화 150자 제한)
- `char_chat/<캐릭터이름>/guide.md`: 유저가 재미있게 말을 걸 수 있도록 공략 팁을 보강합니다.
- `char_chat/<캐릭터이름>/assets/`: 프로필 썸네일(`thumbnail.webp`) 및 상황 이미지(`situation.webp`)를 배치합니다.

### 3단계: 규격 및 글자수 린트 검증
```bash
python3 scripts/checks/check_character_limits.py <캐릭터챗_경로>

# 예시:
python3 scripts/checks/check_character_limits.py examples/apocalypse/char_chat/서린
```

### 4단계: Playwright 자동 주입 및 임시저장
```bash
# 1. 터미널 미리보기
python3 tools/sync/crack_character_sync.py inspect examples/apocalypse/char_chat/서린

# 2. 크랙 에디터 자동 주입 및 임시저장
tools/.venv-sync/bin/python tools/sync/crack_character_sync.py sync examples/apocalypse/char_chat/서린 --headless --auto --auto-submit

# 3. 기존 캐릭터 업데이트 재주입 시 (--url 사용)
tools/.venv-sync/bin/python tools/sync/crack_character_sync.py sync examples/apocalypse/char_chat/서린 --url "https://crack.wrtn.ai/builder/character?..." --headless --auto --auto-submit
```

---

## 4. 1:1 대화 프롬프트 작성 시 주의사항

1. **소설식 나레이션 지문 배제**:
   - `*그가 한 발자국 다가오며 차가운 눈빛으로 올려다보았다*` 와 같은 3인칭 소설식 지문을 프롬프트에서 최소화하고, 캐릭터가 유저에게 실시간으로 말을 건네는 **구어체/메신저 발화** 위주로 지침을 구성합니다.
2. **타이트한 2,000자 예산 관리**:
   - 스토리챗(7,000자) 대비 1/3 이하이므로, 장황한 세계사나 설정 나열을 걷어내고 **① 어투와 말투 습관**, **② 유저와의 관계와 태도**, **③ 절대 깨지지 않는 성격적 모순점** 세 가지만 강하게 압축합니다.
3. **유저 발화(150자)와 호흡 매칭**:
   - 인트로와 예시대화에서 캐릭터 발화가 150자를 넘지 않도록 문장을 간결하고 탄력 있게 주고받는 템포를 잡습니다.
