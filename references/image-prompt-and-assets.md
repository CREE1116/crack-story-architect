# 6. 이미지 프롬프트 및 에셋 제작 바이블 (Image Prompts & Assets)

이 문서는 **전용 이미지 툴체인(`tools/images/`)**을 활용하여 단부루 태그를 검색·검증하고, 배경 프롬프트를 컴파일하며, 생성된 배경을 크랙 규격에 맞게 크롭·변환하여 프로덕션 에셋을 완성하는 공식 지침입니다.

---

## 1. 이미지 제작·태깅·배경 전용 툴체인 (`tools/images/`)

프로젝트 루트의 `tools/images/` 디렉터리에 이미지 제작 및 후처리를 자동화하는 핵심 도구가 내장되어 있습니다.

| 도구명 | 핵심 기능 | 실행 예시 |
|---|---|---|
| **`search_tag.py`** | 단부루 공식 위키 태그 검색 & 동의어/정의 확인 | `python3 tools/images/search_tag.py "smile"` |
| **`compose_scene.py`** | **배경 프롬프트 컴파일러** (5대 앵커 조립, 인물 유출 차단, scene-design.md 생성) | `python3 tools/images/compose_scene.py --parse-story story.md` |
| **`crop_backgrounds.py`** | **배경 크롭·리사이즈 도구** (1024x400 규격화, 배지, WebP 변환, 순서 네이밍) | `python3 tools/images/crop_backgrounds.py --src 원본 --out scene` |
| **`compose_character.py`** | 캐릭터 외형 태그 검증 & `characters.json` 컴파일러 | `python3 tools/images/compose_character.py --parse-md characters.md` |
| **`deploy.py`** | WebP 변환, 에셋 검사, 웹 템플릿 생성, GitHub+jsDelivr 이미지 배포 | `python3 tools/images/deploy.py --convert-webp --root deploy/` |
| **`name_card_cinematic.py`** | **시네마틱 명함** (배경 포함 차분 컷 + 소속·이름·영문 이름·이능 조판, 1200x600) | `uv run tools/images/name_card_cinematic.py img --meta cards.json --out img/명함` |
| **`pages_bundle.py`** | **Cloudflare Pages 번들·배포·전수 검증** (한글 파일명 → s00/s01/a01/bg 코드, 매핑표, 404.html, HEAD 검증) | `python3 tools/images/pages_bundle.py deploy --config build/assets/pages-bundle.json --project <이름>` |
| **`make_cover.py`** | **표지(1080x1620)·배너(1200x400) 합성** (isnet-anime 누끼 또는 `--direct`, 제목·CTA·장식, Chrome 렌더) | `python3 tools/images/make_cover.py 원본.png --out output/banner --kind banner --title "작품명" --direct --dpr 2` |
| **`glitch.py`** | 완성 표지·배너 글리치 후처리 (RGB 분리·슬라이스·틴트 블록, 얼굴 띠 보호) | `python3 tools/images/glitch.py cover.png out.png --level 2 --protect 300:640` |

---

### ① 태그 검색 도구 (`search_tag.py`)
자연어 영어를 임의로 추측해 넣으면 NovelAI나 이미지 생성 모델에서 무시되거나 원치 않는 왜곡이 발생합니다. 반드시 **로컬 Danbooru 위키 데이터베이스(`wiki.sqlite3`)**를 검색해 검증된 공식 태그를 사용합니다.

```bash
# 기본 검색 (태그명, 동의어, 위키 정의 동시 검색)
python3 tools/images/search_tag.py "smile"

# 복수 단어 동시 검색
python3 tools/images/search_tag.py "military jacket" "katana"

# 위키 본문 전체 포함 검색 (--body)
python3 tools/images/search_tag.py "tsundere" --body
```
* **밑줄(`_`) ➔ 공백(` `) 변환**: `black_hair`는 프롬프트에 `black hair`로 자동 치환.
* **동의어 자동 매핑**: 일본어(`ツンデレ`)나 유사어 검색 시 공식 영문 단부루 태그 추천.

---

### ② 배경 제작 컴파일러 (`compose_scene.py`)
`story.md`의 배경/장소 묘사를 자동 파싱하여 5대 앵커(인물 배제, 건축, 조명, 대기, 랜드마크)를 린팅하고, 장소별 프롬프트 명세서(`scene-design.md`)를 추출합니다.

```bash
# 1. story.md 기반 전체 배경 장소 자동 파싱 및 명세서 생성
python3 tools/images/compose_scene.py \
  --parse-story <작품>/story.md \
  --output-md <작품>/build/assets/scene-design.md

# 2. 단일 씬 즉시 컴파일 (CLI 대화형 또는 인자 전달)
python3 tools/images/compose_scene.py \
  --name "지하 방공호 지휘실" \
  --category indoor \
  --arch "underground bunker, reinforced concrete walls" \
  --props "monitors, tactical map on table, steel chairs" \
  --lighting "dim fluorescent lighting, cool moody tone"

# 3. 인물 키워드 누출(Human Leak) 자동 감지
# '1girl', 'smile', 'standing' 등 배경에 인물이 들어가는 태그를 검출하여 경고하고 Scenery UC를 강제 주입
```

---

### ③ 배경 크롭 & 리사이즈 도구 (`crop_backgrounds.py`)
생성된 원본 이미지(1216x832, 1920x1080 등)를 크랙 상단 배경 표준 와이드 규격(`1024x400`, 2.56:1 비율)으로 일괄 크롭하고, 순서에 맞춰 자동 명명 및 WebP로 변환합니다.

```bash
# 1. 원본 이미지를 1024x400 크롭하여 bg01.webp~bg25.webp 변환
python3 tools/images/crop_backgrounds.py \
  --src <원본배경폴더> \
  --out <작품>/deploy/scene \
  --size 1024x400 \
  --format webp

# 2. 마크다운 배치표(에셋_배치표.md) 기반 매칭 및 미리보기(dry-run)
python3 tools/images/crop_backgrounds.py \
  --src image-배경_원본 \
  --out deploy/scene \
  --table image/에셋_배치표.md \
  --dry-run

# 3. 앵커 조절 및 배지 옵션
# --anchor top/center/bottom: 상단/중앙/하단 기준 크롭
# --no-badge: 이미지 좌하단 장소명 텍스트 배지 합성 비활성화
# --format both: PNG와 WebP를 동시 출력
```

---

### ④ 캐릭터 외형 컴파일러 (`compose_character.py`)
`characters.md`의 인물 묘사를 파싱하여 헤어 3요소, 눈동자, 체형, 복장 전 파츠 색상 결속 여부를 린팅하고 `characters.json` 및 `character-design.md`를 생성합니다.

```bash
# characters.md 파싱 및 characters.json 컴파일
python3 tools/images/compose_character.py \
  --parse-md <작품>/characters.md \
  --output-json <작품>/build/assets/characters.json \
  --output-md <작품>/build/assets/character-design.md
```

---

### ⑤ 시네마틱 명함 (`name_card_cinematic.py`)
캐릭터 소개용 명함을 만든다. 누끼형 `name_card.py`와 달리 **배경이 있는 차분 컷을 그대로** 쓴다. 인물을 확대해 오른쪽에 두고, 왼쪽을 어둡게 페이드시켜 그 위에 글자를 얹는다. 차분 컷에 장소 배경이 이미 들어가 있어 누끼를 뜨면 오히려 정보가 줄어들 때 쓴다.

```bash
uv run tools/images/name_card_cinematic.py <작품>/img \
  --meta cards.json --out <작품>/img/명함 [--overwrite]
```

`cards.json` 은 JSON 배열이다. `name`·`source`·`affiliation`·`ability`는 필수, `ability_label`(기본 `이능`)·`roman`·`accent`·`id`는 선택이다.

```json
[{"name": "강연", "source": "강연/차분.png", "affiliation": "하운드 · 길드장",
  "ability": "마킹", "roman": "KANG YEON", "accent": "#E0304A"}]
```

- **카드에는 소속·이름·영문 이름·이능만 넣는다.** 대사, 성격 설명, 작품 제목은 넣지 않는다. 대사는 카드를 읽는 흐름을 끊고, 제목은 가제가 바뀌면 카드를 전부 다시 만들어야 한다.
- **스포일러는 표면 정보로만 적는다.** 정체를 숨긴 인물은 작중 공개 신분(`무소속 · 민간인`, `소속 불명`, 이능 `미등록`)으로 적는다. `숨긴 것` 항목은 카드에 옮기지 않는다.
- 신격이나 이능 체계 밖 존재는 `ability_label`을 `권능` 등으로 바꾼다. 소속은 `○○의 여신`처럼 짧게 쓴다. `원초 여신` 같은 조어 직함은 어색하게 읽혀 반려된 적이 있다.
- `accent`는 소속별 시각 언어 색을 쓴다. 같은 소속은 같은 색이고, 무소속은 인물마다 한 색을 준다. 색은 얇은 선, 모서리 표시, 영문 이름, 왼쪽 글로우에만 쓴다. 굵은 색 바나 채운 면으로 쓰면 유치해 보인다.
- 인물 중심은 x=800에 오고, 페이드는 x=820에서 투명도 0이 되므로 얼굴에는 레이어가 닿지 않는다. `source` 컷의 인물이 화면 중앙에 있어야 이 좌표가 맞는다. 인물이 한쪽으로 치우친 컷은 차분 컷을 다시 뽑거나 다른 컷을 쓴다.
- 서체: 이름은 Noto Serif KR Black, 영문 이름은 Cinzel Bold(자간 7), 소속과 라벨은 IBM Plex Sans KR이다. 모두 OFL 라이선스이고, 첫 실행 때 `~/.cache/crack-story-fonts`로 내려받는다.
- 다 만든 뒤 전체를 한 장에 모아 보고, 이름 길이(2~3자와 4자 이상)와 밝은 배경 컷에서 글자가 읽히는지 확인한다.

---

## 2. 캐릭터 베이스 프롬프트와 가감(+a / -소거) 원칙

### 💡 이미지 태그는 '불변(Immutable)'이 아닙니다
> 캐릭터의 베이스 프롬프트(기본 외형 및 대표 복장)는 인물의 시각적 정체성을 규정하는 **출발점(Anchor)**일 뿐이며, 모든 생성에서 토씨 하나 바꾸지 않는 '불변의 텍스트'가 아닙니다.
> 장면에 따라 **새로운 태그가 추가(+a)**되거나, **기존 태그가 일시 제외(-소거)**되어 생성 모델에 투입됩니다.

```
[1. 품질/기본 앵커]
masterpiece, best quality, ultra-detailed, 1girl (또는 1boy), solo
       ↓
[2. 인물 고유 식별 앵커 (헤어 + 눈동자 + 기본 체형)]
long straight black hair, red eyes, slender athletic build, medium breasts
       ↓
[3. 기본 대표 복장 & 장비 (가변적 출발점)]
black tactical turtleneck, military jacket, cargo pants, combat boots, katana on back
       ↓
[4. 씬별 가감(+a / -소거) 및 표정/연출 결합]
- 일상/대화: 기본 복장 유지 + [soft smile, slight blush, eye contact]
- 전투/피격: 기본 복장 + [torn clothes, blood, scratches, dynamic combat stance] (+a 추가)
- 복장 교체: 기존 아우터/바지 소거 ➔ [hoodie, denim shorts] 또는 [pajamas] (교체)
- 성인 씬: 의상/장비 전면 소거 ➔ [nude, spread legs] + 체위 및 성애 상황 태그 결합
```

### 📌 태그 가감(+a / -소거)의 4대 실전 운용
1. **손상 및 전투 상태 (+a)**:
   - 교전 중이거나 위기 상황에서는 `torn clothes, scratched skin, blood on cheek, disheveled hair, dirt, dust particles` 등을 추가(+a)합니다.
2. **날씨 및 환경 상호작용 (+a)**:
   - 비, 눈, 물에 젖은 상황에서는 `wet clothes, soaked hair, dripping water, shivering` 등을 추가(+a)합니다.
3. **복장 교체 및 탈의 (-소거 및 대체)**:
   - 실내 휴식, 잠자리, 수영장, 사복 씬에서는 베이스의 군복/전투복 태그를 소거(-)하고, `jacket off, sleeveless, pajamas, swimsuit, underwear` 등으로 대체합니다.
4. **간섭 방지 소거 (Glitch Guard)**:
   - 복잡한 신체 접촉, 포옹, 성애 체위, 손 클로즈업 등에서 기존의 '등에 멘 무기(`katana on back`)', '전술 배낭', '모자' 태그가 남아있으면 신체 부위가 기형으로 융합되는 글리치가 발생합니다. 이런 씬에서는 **방해되는 복장/소품 태그를 과감히 소거(-)**해야 합니다.

---

## 3. `build/assets/characters.json` 작성 규격 (GREED 표준)

이미지 생성 파이프라인의 인물 정본으로, **NovelAI 가중치 문법(`1.35::...::`)**이 적용된 완성형 베이스 프롬프트와 인물별 외형 이탈 방지 네거티브(`uc`)를 소유합니다:

```json
[
  {
    "name": "유라",
    "prompt": "1girl, solo, mature female, 31yo, master craftsman, 1.35::dark auburn hair, long hair, low ponytail tied with copper wire, loose sidelocks, strand of hair tucked behind ear::, 1.35::amber eyes, tareme, faint soot smudge on cheek::, 1.3::fair skin, 166cm, slender, lean arms, small breasts, narrow waist, long legs::, 1.35::burn scars on both hands, small cut scars on fingers::, 1.35::black turtleneck with sleeves pushed up, heat-resistant grey welding sleeve on left arm only, charcoal cargo work pants, worn dark brown leather apron with brass rivets, brown leather tool belt with wrenches, black steel-toed boots::, 1.35::long metal tool staff, amber glowing cache crystal set in the staff head, copper wiring wrapped around the grip::, welding goggles hanging around neck",
    "uc": "loli, child, kid, chibi, super deformed, lowres, bad anatomy, bad hands, extra digits, fewer digits, worst quality, low quality, signature, watermark, very short hair, buzz cut, undercut, shaved sides, short hair, black hair, goggles on head, makeup, lipstick, jewelry, earrings, dress, skirt, cleavage, huge breasts, bright colors"
  }
]
```

### 📌 가중치 문법 & UC 작성 규칙
1. **가중치 문법 (`1.35::...::`)**:
   - `1.35::헤어 3요소::`: 헤어스타일과 색상이 다른 인물과 섞이지 않도록 최우선 락.
   - `1.35::눈동자 + 시선::`: 동공 색상과 눈매 락.
   - `1.3::체형 + 키::`: 체격과 키, 가슴 크기 락.
   - `1.35::대표 복장::`: 고유 의상 락.
   - `1.35::시그니처 무기/장비::`: 고유 소품 락.
2. **맞춤형 네거티브 (`uc`)**:
   - 기본 품질 가드(`lowres, bad anatomy, ...`) 뒤에 **그 인물에게 절대 나타나면 안 되는 반대 속성**을 명시합니다. (예: 흑발이면 `blonde hair`, 슬림 체형이면 `huge breasts, cleavage`, 제복이면 `dress, skirt`).

---

## 4. 장면 및 배경 프롬프트 작성법 (Scene & Environment)

배경 프롬프트는 **① 풍경화형 단독 배경(Pure Scenery)**과 **② 인물 결속형 배경(Staged Environment)**의 2대 갈래로 나뉩니다.

### 갈래 A: 풍경화형 단독 배경 (Pure Scenery CG)
공간 이동, 씬 전환, 프롤로그 원경 등에 쓰이는 인물 없는 웅장한 배경입니다:
```text
[5대 필수 앵커]
1. 인물 배제 락: no humans, scenery, landscape
2. 공간 스케일 & 건축: wide panoramic view, ruined city, overgrown skyscrapers, cracked asphalt road
3. 시간대 & 조명: overcast grey sky, volumetric sunbeams breaking through clouds, dim moody lighting
4. 대기 & 환경 입자: atmospheric haze, floating dust particles, rusted abandoned cars, creeping ivy
5. 랜드마크: massive collapsed bridge in background, destroyed convenience store in foreground
```

### 갈래 B: 인물 결속형 배경 (Staged Character Environment)
캐릭터 포트레이트 뒤에 합성되거나 캐릭터와 함께 생성되는 인간 스케일의 생활/전투 공간입니다:
```text
[4대 필수 앵커]
1. 실내/야외 공간 바인딩: indoors, underground bunker hideout, reinforced concrete walls
2. 인물 지지대 (가구/벽): leaning against metal locker, sitting on worn leather chair, beside wooden crate
3. 인물 지향 조명: cool fluorescent light from ceiling, warm lantern glow on subject, dramatic rim lighting
4. 피사계 심도 (Depth): depth of field, blurred background, bokeh, medium shot
```

---

## 5. 이미지 코드 규약과 프롬프트 출력 규칙

### ① 코드 규약 (배포 전 반드시 코드명으로 바꾼다)

한글 파일명(`공포_겁먹음.webp`)을 그대로 URL 에 쓰지 않는다. 모델이 한글 경로를 틀리게 쓰고, 프롬프트 글자 수도 잡아먹는다. 원본은 그대로 두고 `pages_bundle.py` 가 배포 폴더에 코드명으로 복사한다.

| 경로 | 뜻 |
|---|---|
| `<식별번호>/s00.webp` | 명함 (첫 등장) |
| `<식별번호>/s01~.webp` | 전연령 감정·상황 컷. 전 인물 공통 순서 |
| `<식별번호>/a01~.webp` | 성인 컷 (19+ 판에서만 호출) |
| `bg/bgNN.webp` | 배경 |
| `<묶음>/rNNe.webp`, `rNNb.webp` | 몬스터·이벤트 묶음 (예: 출현 e / 공격 b) |

- **식별번호 = 프롬프트 명부 순서.** 명부 줄 앞에 `▶01이름` 처럼 번호를 박아 모델이 번호를 추측하지 않게 한다. 숨은 인물(반전용)도 명부 뒤쪽 번호를 받는다.
- **코드 순서는 전 인물 공통.** 인물마다 가진 컷이 다르면(예: 한 명만 전투2) `aliases` 로 같은 코드에 묶고, 아예 없는 컷은 프롬프트에 예외로 적는다("15는 s11까지").
- 성인 컷 중 **노출이 있는 컷은 s 가 아니라 a** 로 분류한다. 파일명(예: '유혹')만 보고 판단하지 말고 실제 이미지를 확인한다.
- 원본 폴더를 macOS 에서 읽으면 파일명이 NFD 로 온다. 비교는 NFC 정규화 후에 한다(`pages_bundle.py` 가 처리).

### ② 통합 프롬프트 출력 규칙 (압축형 템플릿)

```markdown
# N. 이미지 출력(必)
- {IMG}=https://<프로젝트>.pages.dev｜번호=▶이름 앞 2자리｜무명·ⓤ×.
- 장소 진입時 본문 첫 줄 `![배경]({IMG}/bg/bgNN.webp)`: 01로비 02측정실 … (짧은 장소명)
- ⓒ 대사마다 직전 `![이름]({IMG}/번호/코드.webp)`. 첫 등장=s00(명함),이후=그 대사 감정: s01차분 s02호감 … (예외 인물의 보유 범위). 동일 코드 연속×.
- 몬스터 첫 출현 `![이름]({IMG}/ray/rNNe.webp)`·첫 공격 rNNb(NN=§N 순번).
```

- 7K 예산이 모자라면 **성인 a 코드표는 🔞 신호로 켜지는 키워드북 항목**(성애 연출)에 합친다. 🔞 는 성애 장면에서만 켜지므로 그때만 필요한 정보와 수명이 같다. 단, 키워드북 20항목 상한 때문에 별도 항목을 늘리지 말고 기존 🔞 항목에 합친다.
- 몬스터 번호는 세계관 섹션의 개체 나열 순서에 그대로 박는다(`D 01크롤러·02러너…`). 따로 범례를 두지 않아도 된다.

### ③ 명함이 이름을 드러내는 문제

명함(s00)에는 이름이 조판되어 있다. **플레이어가 아직 이름을 모르는 인물**(정체불명 조력자 등)은 첫 등장에도 명함을 쓰면 안 된다.

- 해당 시작 세트 start-prompt 에 "이름 밝히기 전 명함(s00) 禁·alt 는 공개 호칭·감정 코드만" 을 적는다.
- 재등장 트리거가 있는 키워드북 항목에도 같은 문구를 넣는다. 인물 항목은 `**이름**|` 발화 표기로 켜지는데, 이름을 모르는 동안에는 공개 호칭으로 불려 그 항목이 안 켜지기 때문이다.

### ④ 프롤로그·시작 상황에 이미지 넣기

- 프롤로그는 사람이 쓴 원고라 이미지를 직접 박는다. 맨 위에 배경, 장면이 바뀌는 문단 앞에 새 배경, 이름 있는 인물 대사 바로 앞에 인물 컷.
- 이름을 가린 채 등장하는 인물(예: "짐벌 든 신인")도 프롤로그에서는 alt 를 그 호칭으로 두고 얼굴 컷을 먼저 보여줄 수 있다. 이 경우 start-prompt 에 "정식 첫 대사 직전 s00" 을 적어 명함이 뒤에 한 번 나오게 한다.
- start-prompt 에는 첫 턴의 이미지 지시(유지할 배경, 이동 시 바꿀 배경, 첫 등장 인물 명함, 몬스터 컷)를 한 줄로 둔다.
- 넣은 URL 은 `check_image_urls.py` 가 배포 목록과 대조한다.

## 6. 호스팅·소개 사이트·배너로 이어가기

[hosting-showcase-and-banner.md](hosting-showcase-and-banner.md)를 읽는다. Cloudflare Pages 는 `pages_bundle.py`(§6), GitHub+jsDelivr 는 `deploy.py` 를 쓴다. `deploy.py --convert-webp`는 PNG/JPEG 원본을 보존하고 기존 WebP와 충돌하면 중단한다. `--scaffold --asset-gallery`로 만드는 범용 갤러리는 공개 온보딩 사이트가 아니다.
