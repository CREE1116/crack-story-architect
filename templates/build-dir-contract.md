# build/ — 컴파일 산출물

이 디렉터리는 **손으로 쓰는 곳이 아니다.** `story.md`·`characters.md`와 `start-sets/`에서
매번 다시 생성한다. 아래 6개 파일이 정확히 있어야 하고, 그 외의 파일을 두지 않는다.
(`assets/`만 예외로 허용된다.)

| 파일 | 상한 | 출처 |
|---|---|---|
| `integrated-prompt-safe.md` | ≤ 7,000자 | `references/master-prompt-template.md` |
| `integrated-prompt-unsafe.md` | ≤ 7,000자 | 위와 동일. 섹션 제목은 SAFE와 일치해야 한다 |
| `keyword-book-safe.md` | 항목당 UTF-16 ≤ 400자 | `references/keyword-book-guide.md` |
| `keyword-book-unsafe.md` | 항목당 UTF-16 ≤ 400자 | 위와 동일 + 성애 연출 모듈 |
| `prologue.md` | ≤ 1,000자 | `start-sets/01_default/prologue.md` 사본 |
| `start-prompt.md` | ≤ 1,000자 | `start-sets/01_default/start-prompt.md` 사본 |

`assets/`에는 크랙 웹 등록용 파생물과 이미지 프롬프트가 들어간다.
전체 규격은 `references/platform-spec-and-lint.md`, 완성된 실물은 `examples/apocalypse/build/`를 본다.

검증:

```bash
./scripts/validate.sh <project>
```
