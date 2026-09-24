# 표지·배너 폰트 (선택)

`make_cover.py` 가 쓰는 폰트. 용량(약 30MB) 때문에 저장소에 넣지 않는다.
없으면 시스템 폰트로 대체되어 렌더는 되지만 제목 인상이 달라진다.

| 파일 | 용도 | 받는 곳 (모두 SIL OFL) |
|---|---|---|
| `Cinzel-VF.ttf` | 영문 제목·장식 문자 | https://fonts.google.com/specimen/Cinzel |
| `NotoSerifKR-VF.ttf` | 한글 부제·CTA 버튼 | https://fonts.google.com/noto/specimen/Noto+Serif+KR |
| `IBMPlexSansKR-SemiBold.ttf` | 바코드 숫자·라벨 | https://fonts.google.com/specimen/IBM+Plex+Sans+KR |

이 폴더에 두거나, 다른 위치라면 `CRACK_FONT_DIR=/path/to/fonts` 로 지정한다.
