# crack_sync — 크랙 스튜디오 자동 입력

`build/` 산출물(프롬프트·시작 세트·키워드북·단축어·상세설명·등록 탭)을 크랙 에디터에 채우고 임시저장한다.
발행은 하지 않는다. 고정 댓글(`summary-comment.md`)은 발행 후 사람이 직접 붙인다.

## 준비

```bash
python3 -m venv tools/.venv-sync
tools/.venv-sync/bin/pip install playwright
tools/.venv-sync/bin/python -m playwright install chromium
tools/.venv-sync/bin/python tools/sync/crack_sync.py auth      # 최초 1회 로그인 (브라우저 창)
```

로그인 상태는 `~/.crack/profile` 에 남는다. 같은 프로필을 두 프로세스가 동시에 쓰면 잠금으로 실패하므로 SAFE·UNSAFE 는 순서대로 돌린다.

## 사용

```bash
P=<프로젝트>
PY=tools/.venv-sync/bin/python
$PY tools/sync/crack_sync.py inspect $P --variant unsafe          # 글자 수·항목 수 미리보기
export CRACK_SYNC_THUMBNAIL="$P/thumbnail.webp"                    # 1080x1620, 5MB 미만. 신규 생성에 필수
$PY tools/sync/crack_sync.py sync $P --variant safe   --headless --auto --auto-submit   # 새 작품 생성
$PY tools/sync/crack_sync.py sync $P --variant unsafe --headless --auto --auto-submit \
    --url "https://crack.wrtn.ai/builder/story?type=create&storyId=<ID>&step=detail"      # 기존 작품 재주입
```

- 새 작품 생성 시 로그 끝의 `🔗 이 작품의 에디터 주소` 에서 storyId 를 기록해 두고, 다음부터는 `--url` 로 같은 작품에 재주입한다. URL 없이 돌리면 매번 새 작품이 생긴다.
- 헤디드(기본) 모드는 입력 대기 루프에 들어가므로 에이전트·백그라운드 실행에는 `--headless --auto --auto-submit` 을 쓴다.

## 겪은 함정

| 증상 | 원인 / 대처 |
|---|---|
| 제목이 `작품명 U U` | `story.md` Core 의 `- Unsafe title suffix: U` 가 이미 unsafe 제목에 붙는다. `--title-suffix` 를 같이 주지 않는다 (현재는 중복 방지됨). |
| `키워드북 상한(20개)에 걸려 20개만 등록` | 크랙 키워드북은 **20항목 상한**(단축어 제외). 넘친 뒤쪽 항목은 조용히 빠진다. `check_keyword_book.py` 가 FAIL 로 잡는다. 항목을 합쳐서 줄인다. |
| `⛔ [대표 이미지] 가 비어 있습니다` | 신규 작품은 표지가 없으면 저장이 거부된다. `CRACK_SYNC_THUMBNAIL` 지정. |
| `⚠️ [권장 최대 출력량] 칸을 찾지 못했습니다` | 현재 UI 에서 자동 입력 불가. 에디터에서 직접 선택. |
| `[임시저장] 버튼 클릭 실패: Timeout` | 첫 시도가 모달에 가려진 경우. 도구가 재시도하며 `새로고침 후에도 제목이 남아 있음` 이 뜨면 저장된 것. |
| `❌ Playwright가 설치되지 않았습니다` | 시스템 python3 가 아니라 위 venv 의 python 으로 실행. |
| zsh 에서 `for pair in "safe ID" ...; set -- $pair` 가 안 쪼개짐 | zsh 는 기본 단어 분리를 안 한다. `bash -c '...'` 로 감싸거나 변수를 따로 둔다. |
