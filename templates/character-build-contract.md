# Character Chat build/ Contract — 컴파일 산출물 규격

이 디렉터리는 캐릭터챗의 정본 소스(`character.md`, `dialogues.md`, `guide.md`, `meta.yaml`)로부터 컴파일 생성되는 자동 주입용 결과물 폴더입니다.
Playwright 동기화 도구(`crack_character_sync.py`)는 이 디렉터리의 데이터를 읽어 크랙 웹 에디터에 주입합니다.

## 필수 산출물 파일 목록 및 규격

| 파일명 | 최대 글자 수 / 수량 | 설명 | 출처 파일 |
|---|---|---|---|
| `prompt.md` | **≤ 2,000자** | 시스템 프롬프트 (캐릭터 페르소나, 대화 규칙, 관계성) | `character.md` |
| `play-guide.md` | **≤ 500자** | 유저 플레이 가이드 (대화 시작 팁) | `guide.md` |
| `character-desc.md` | **≤ 1,000자** | 캐릭터 상세 설명문 | `guide.md` |
| `intro.json` | 각 발화 **≤ 150자** | 인트로 대화 1세트 (`{"user": "...", "character": "..."}`) | `dialogues.md` |
| `examples.json` | 각 발화 **≤ 150자**, **최대 10개** | 예시 대화 목록 (`[{"user": "...", "character": "..."}, ...]`) | `dialogues.md` |
| `meta.json` | 이름/한줄소개 **≤ 30자** | 이름, 한줄소개, 장르, 타겟, 해시태그 | `meta.yaml` |

## 에셋 파일 (선택 및 권장)
- `assets/thumbnail.webp` (또는 `.png`, `.jpg`): 대표 프로필 이미지 (크랙 규격 권장)
- `assets/situation.webp` (또는 `.png`, `.jpg`): 채팅방 상황/배경 이미지 (선택)

## 검증 명령어
```bash
python3 scripts/checks/check_character_limits.py <프로젝트경로>
```
