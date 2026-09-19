# templates/

| 경로 | 내용 |
|---|---|
| `story-chat-template/` | 새 프로젝트의 **빈 양식**. 복사해서 시작한다. `story.md`, `characters.md`, `start-sets/` 뿐이다. |
| `build-dir-contract.md` | 컴파일 후 `build/`에 정확히 무엇이 있어야 하는가 |
| `build-assets-contract.md` | `build/assets/`의 파생 에셋 규격 |

```bash
cp -r templates/story-chat-template ~/my-story
```

`build/`는 손으로 만들지 않는다. Phase 2 컴파일이 생성한다.
완성된 실물 참조는 [`examples/apocalypse/`](../examples/apocalypse/)를 본다.
