# Character Chat Template

캐릭터 1명과 1:1로 채팅(대화)하는 감각의 크랙 캐릭터챗 제작 템플릿입니다.

## 파일 구성
- `character.md`: 캐릭터의 외모, 말투, 심리, 유저와의 관계 및 호감도 변화 정의
- `dialogues.md`: 인트로 대화(1세트) 및 Few-shot 예시대화(최대 10세트)
- `guide.md`: 플레이가이드(500자) 및 캐릭터 설명(1000자)
- `meta.yaml`: 이름(30자), 한줄소개(30자), 장르, 타겟, 해시태그
- `assets/`: 대표 이미지 및 상황 이미지

## 제작 및 동기화 흐름
1. 기획 작성: 위 파일들을 작성합니다.
2. 빌드 컴파일: `build/` 디렉터리에 규격 파일들 생성
3. 검증: `python3 scripts/checks/check_character_limits.py .`
4. 크랙 주입: `tools/.venv-sync/bin/python tools/sync/crack_character_sync.py sync . --headless --auto --auto-submit`
