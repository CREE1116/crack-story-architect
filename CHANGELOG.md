# Changelog

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
