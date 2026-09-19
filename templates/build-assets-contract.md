# build/assets/ — 파생 에셋

크랙 웹 등록용 산출물과 이미지 파이프라인 입력이 들어간다. 여기의 파일은 모델 프롬프트로
올라가지 않는다. 규격은 `references/derived-assets-and-showcase.md`와
`references/image-prompt-and-assets.md`에 있고, 완성된 실물은 `examples/apocalypse/build/assets/`에 있다.

| 파일 | 용도 | 상한 |
|---|---|---|
| `story-description.md` | 크랙 상세설명란 (마크다운 3대 블록) | — |
| `summary-comment.md` | 첫 고정 댓글 (플레인 텍스트 4대 블록) | — |
| `play-guide.md` | [시작 설정] 탭 플레이어 안내문 | ≤ 500자 |
| `recommended-replies.md` | 세트 공통 첫 추천 답변 3종 (`---` 구분) | 항목당 ≤ 30자 권장 |
| `characters.json` | NovelAI 가중치 베이스 프롬프트 + UC | — |
| `prompts.json` | 기계 판독용 이미지 프롬프트. 슬러그의 단일 출처 | — |
| `image-prompts.md` | 단부루 검증 태그 기반 일러스트 시트 | — |
| `character-design.md` | 인물 시각 디자인 명세표 | — |
| `scene-design.md` | 배경·장면 시각 디자인 명세표 | — |
| `build-stamp.json` | 컴파일 시점 원본 해시 (`check_freshness.py --stamp`가 생성) | — |
