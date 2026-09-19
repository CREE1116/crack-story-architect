# Changelog

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
