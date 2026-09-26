# Changelog

## 1.5.0 — 2026-09-26

「시청 중인 성좌」 캐릭터 외형 작업에서 반복된 실패(색 부조화, 흑발 과다, 긴 프롬프트의 그림체 붕괴, 웨이터·백화점 룩)를 지침과 검사기로 옮겼다.

### 추가
- `references/character-visual-design.md`: 캐스트 표 → 세력 룩(공통 표식 vs 개인 욕망) → 세계 공통 팔레트·60-30-10 → 헤어 → 눈매 → 체형 → 의상·소품 → 겹침 검사 → 컴파일 → UC → 정본 동기화 순서. 단부루 위키 DB로 존재를 확인한 헤어·눈매·얼굴·체형 태그 카탈로그와, 위키가 없는 흔한 표현(`low bun`, `fluffy hair`, `slender`, `hourglass figure` 등) 목록. 오해 조합 표, 검수 체크리스트.
- `scripts/checks/check_character_prompts.py`: 키 규격, 600자 FAIL·450자 WARN, 가중치 짝·개수, 자연어 `.,` 종결과 문장 내 쉼표, 표정·배경·나이·cm 혼입, prompt↔uc 충돌, 헤어 묶음 중복, uc의 표정 태그·prompt 안 중복 태그(WARN). `validate.sh`에 연결.
- 단위 테스트 `scripts/checks/tests/test_character_prompts.py`.

### 수정
- `references/image-prompt-and-assets.md` §3: 가중치 5곳·나이/키 숫자·장문 예시를 폐기하고 새 규격 요약으로 교체.
- `examples/apocalypse/build/assets/characters.json`: 새 규격으로 재작성.
- `SKILL.md`: 라우팅 맵과 검사기 표에 추가.

## 1.4.0 — 2026-09-25

GREED 배포 과정에서 만든 도구와 겪은 함정을 반영했다.

### 추가
- `tools/images/pages_bundle.py`: 한글 원본 파일명을 설정 JSON 대로 코드명(`<번호>/s00`, `s01~`, `a01~`, `bg/bgNN`, 몬스터 묶음)으로 복사해 사이트·배너와 함께 Cloudflare Pages 에 올리고, 배포된 전 파일을 HEAD 로 검증한다. NFD 파일명 정규화, 오타 별칭, 코드 충돌 중단, `404.html` 자동 생성(없으면 없는 경로가 200 으로 숨음), Cloudflare 403 을 피하는 User-Agent.
- `tools/images/make_cover.py`·`glitch.py`: 표지(1080x1620)·배너(1200x400) 합성과 글리치 후처리. 팔레트·CTA·장식 글자를 인자로 받고, 폰트는 선택 설치(`fonts/README.md`).
- `tools/sync/crack_sync.py`: 레퍼런스가 가리키던 크랙 스튜디오 자동 입력 도구를 저장소에 포함. `--title-suffix` 와 story.md 선언이 겹쳐 `U U` 가 되던 문제 수정. `tools/sync/README.md` 에 설치·헤드리스 사용·함정 정리.
- `scripts/checks/check_image_urls.py`: 프롤로그·시작 상황·상세설명·댓글에 박힌 이미지 URL 을 배포 매핑표와 대조.
- 단위 테스트: `test_keyword_book.py`, `test_image_urls.py`, `test_pages_bundle.py`.

### 수정
- `check_keyword_book.py`: 키워드북 20항목 상한(단축어 제외)을 FAIL 로, 프롬프트·시작 세트·다른 항목 어디에도 없는 키워드를 도달 불가 WARN 으로 잡는다.
- 상세설명 규약: 배너·사이트 링크·이미지 자산 표·단축어만. 세계관 설명·플레이 가이드 금지, 제작자 코멘트는 작성자 몫.
- 고정 댓글 규약: 식별 번호 명부, 이미지 출력 양식과 코드를 한 섹션으로, 상태창 이모지 범례 전부, 구분선으로 가독성.
- 이미지 레퍼런스 §5: 코드 규약, 압축 출력 규칙 템플릿, 성인 코드표를 🔞 항목에 합치는 예산 운용, 명함이 이름을 드러내는 문제, 프롤로그 이미지 배치.
- 키워드북 가이드: 20항목 상한, 발동 경로 설계(도달 불가 키워드, 조건을 먼저 켜지는 곳에 두기, 공개 호칭 인물, 세계명 키워드 금지).
- 원작 가이드: 사건 엔진 단계마다 열리는 조건·의존·시점·인정 범위를 적고, 엔딩은 명시적 선택으로만.
- 시작 세트 가이드: 배포 직전 점검(이미지, 모르는 이름, 추천 답변 순서, 세트 간 날짜·소지금, 빌드 사본).
- 플랫폼 규격: 키워드북 항목 수·대표 이미지 규격, 체크리스트 3항목.

## 1.3.0 — 2026-09-22

### 추가
- 시네마틱 명함 도구 `tools/images/name_card_cinematic.py`. 배경이 있는 차분 컷을 확대해 오른쪽에 두고, 왼쪽 페이드 위에 소속·이름·영문 이름·이능을 조판한 1200x600 카드를 만든다. 서체(Noto Serif KR·IBM Plex Sans KR·Cinzel, OFL)는 첫 실행 때 내려받는다.
- `references/image-prompt-and-assets.md` ⑤ 시네마틱 명함 작성 규칙: 카드 수록 항목, 스포일러 인물 표기, 신격 라벨, 소속 색 사용 범위, 인물 좌표와 페이드 경계, 검수 방법.

### 검증
- GREED 19인 차분 컷으로 렌더해 기존 수작업 카드와 픽셀 비교(필름 노이즈 외 차이 없음).

## 1.1.0 — 2026-09-22

### 추가
- 바로 사용하는 HTML/CSS 온보딩 사이트 3종: 전술 단말기, 길드 게시판, 기록관. 별도 설치나 외부 리소스 없이 동작하며 모바일 레이아웃을 포함한다.
- 작품 연장형 사이트 설계 지침: 기록자·시점·열람 권한, 공개 사실·관측·소문·비밀의 경계, 첫 진입에 필요한 정보만 제공하는 기준.
- 사이트 설계 양식과 템플릿별 디자인·교체 지침.
- 이미지 호스팅·배너 제작·사이트 연결 및 배포 검증 지침.

### 수정
- 상세설명 집계·등록 단축어·공개 정보 검토 절차와 한 줄 소개 예시 글자 수.
- 이미지 변환의 원본 삭제, 웹 스캐폴드의 경로 가정, GitHub+jsDelivr 배포와 Pages 호스팅의 차이를 실제 도구 동작에 맞춰 명시. 도구 코드 자체는 변경하지 않았다.

### 검증
- 예제 프로젝트와 컴파일 전 템플릿 검사, Python 문법, 스킬 형식 검증 통과.
- 사이트 3종의 데스크톱 1280px·모바일 390px 첫 화면 확인, 로컬 링크 검사 및 단말기 안내 펼치기 확인.

## 1.0.1 — 2026-09-18

### 수정
- 플러그인으로 설치했을 때 `SKILL.md`의 경로가 전부 깨지던 문제. 본문이 `./scripts/validate.sh`,
  `templates/`, `examples/` 같은 레포 상대경로를 썼는데, 플러그인 본체는 캐시 디렉터리에 있고
  작업 디렉터리는 유저 프로젝트라 어느 쪽에서도 맞지 않았다. `${CLAUDE_PLUGIN_ROOT}` 기준으로 바꾸고,
  검사기(플러그인 쪽)와 검사 대상(유저 쪽)의 경로를 섞지 말라고 명시했다.

## 1.0.0 — 2026-09-18

`design-crack-story-chat`에서 분리한 독립 레포의 첫 공개 릴리스.

### 추가
- Claude Code 플러그인 매니페스트 (`.claude-plugin/plugin.json`, `marketplace.json`). 루트 `SKILL.md`를 쓰는 단일 스킬 플러그인 규약.
- 검사기 8종 (`scripts/checks/`)과 통합 러너 `scripts/validate.sh`.
  - 신규 `check_keyword_book.py`: 항목당 UTF-16 400자, 키워드 1~5개, `.` 상시 트리거 핵, 단축어 슬래시·이름·설명 한도.
- 완성된 참조 프로젝트 `examples/apocalypse/`. 정본 2개부터 통합 프롬프트·키워드북·파생 에셋까지 전부 채워져 있고 CI가 매 푸시마다 검증한다.
- GitHub Actions `validate` 워크플로. 양성 검사에 더해 음성 대조 3종(미정의 기호·키워드북 초과·원본 변경)을 돌려 검사기 자체가 죽어 있지 않은지 확인한다.
- `LICENSE` (MIT), `requirements.txt`, `CHANGELOG.md`.

### 변경
- `templates/story-chat-template/`를 순수 빈 양식으로 정리했다. 절반만 채워져 있던 아포칼립스 예제 내용은 `examples/apocalypse/`로 옮겼다.
  - `build/` 규약은 `templates/build-dir-contract.md`와 `templates/build-assets-contract.md`로 분리했다. 템플릿 디렉터리 안에 두면 구조 검사가 실패한다.
- `tools/images/`의 단부루 위키 DB 탐색이 이식 가능해졌다. 하드코딩된 개인 절대경로를 제거하고 `CRACK_WIKI_DB` 환경변수를 최우선으로 본다.
- `README.md`에서 개인 절대경로를 전부 제거하고, 설치·빠른 시작·검증 절을 추가했다.
- `SKILL.md`에 검증 게이트와 참조 실물 경로를 추가했다.
