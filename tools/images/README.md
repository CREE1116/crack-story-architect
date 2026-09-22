# 이미지 자산 관리 및 Cloudflare Pages 배포 도구

스토리챗에 사용할 이미지는 단부루 위키 기반의 **초정밀 캐릭터 시각 지문(Visual Fingerprint) 프롬프트**를 구성하고, 제작된 이미지를 WebP로 최적화하여 Cloudflare Pages 및 웹 쇼케이스 갤러리로 서빙하는 통합 툴체인을 제공합니다.

---

## 0. 단부루 공식 태그 검색 및 검증 (`search_tag.py`)

캐릭터의 체형, 헤어, 의상, 눈매 등의 태그를 단부루 2024 공식 위키 DB에서 실시간 검색합니다:

```bash
python3 search_tag.py "thigh gap" "high ponytail" "tactical vest"
```

---

## 0.1. 캐릭터 외형 베이스 프롬프트 컴파일러 (`compose_character.py`)

체형 및 신체 고유 디테일(가슴 볼륨, 근육/탄탄함, 골격 실루엣, 허벅지/골반/쇄골 등), 헤어 3요소(색상+스타일+기장), 의상 전 파츠 색상 결속을 자동 린팅하고 불변 베이스 프롬프트 및 UC(Undesired Content)를 생성합니다:

```bash
# 데모 실행 및 린팅 테스트
python3 compose_character.py --demo

# characters.md 파싱 및 검증
python3 compose_character.py --parse-md <작품>/characters.md
```

---

## 0.2. 배경 및 환경 프롬프트 컴파일러 (`compose_scene.py`)

풍경화형 단독 배경(Pure Scenery CG, 5대 앵커: no humans 락, 공간/건축, 조명/시간, 대기/날씨, 소품/랜드마크, 카메라)과 인물이 결합되는 결속용 배경(Staged Environment: 환경 바인딩, 지지대/가구, 인물 조명, 심도)을 자동 린팅하고 `scene-design.md` 및 `prompts.json`을 생성합니다:

```bash
# 데모 실행 및 5대 앵커 린팅 테스트
python3 tools/images/compose_scene.py --demo

# story.md 기반 배경 장소 자동 파싱 및 명세서 생성
python3 tools/images/compose_scene.py --parse-story <작품>/story.md --output-md <작품>/build/assets/scene-design.md

# 기계 판독용 프롬프트 JSON 내보내기
python3 tools/images/compose_scene.py --parse-story <작품>/story.md --output-prompts-json <작품>/build/assets/prompts.json

# 단일 씬 즉시 컴파일
python3 tools/images/compose_scene.py --name "마왕성 로비" --category indoor --arch "grand corporate lobby" --props "speed gate turnstiles" --lighting "volumetric ceiling lights"
```

---

## 0.3. 배경 이미지 크롭 및 순서 리네이밍 도구 (`crop_backgrounds.py`)

NovelAI 등에서 생성된 원본 이미지(1216x832, 1920x1080 등)를 크랙 스토리챗 상단 배경 표준 와이드 규격(`1024x400`, 2.56:1 비율)으로 Center Crop 및 고품질 Lanczos 리사이즈하고, 마크다운 배치표(`에셋_배치표.md`)나 프리셋 순서에 맞춰 넘버링(`bg01_장소명.webp` 또는 `a01.webp`)을 자동 부여합니다:

```bash
# 마크다운 배치표 기반으로 1024x400 크롭 및 bg01~bg25 네이밍 후 WebP 변환
python3 tools/images/crop_backgrounds.py \
  --src image-배경_원본 \
  --out image/배경 \
  --table image/에셋_배치표.md \
  --format webp

# 미리보기 (dry-run)
python3 tools/images/crop_backgrounds.py --src image-배경_원본 --out image/배경 --table image/에셋_배치표.md --dry-run

# 원본 폴더 전체 일괄 크롭 및 01_이름.webp 저장
python3 tools/images/crop_backgrounds.py --src image-배경_원본 --out image/배경 --style clean

# 크랙 표준 scene/a01 스타일 및 PNG+WebP 동시 저장
python3 tools/images/crop_backgrounds.py --src image-배경_원본 --out deploy/scene --table image/에셋_배치표.md --style scene --format both
```

---

## 0.4. 시네마틱 명함 (`name_card_cinematic.py`)

배경이 있는 차분 컷을 확대해 오른쪽에 두고, 왼쪽 페이드 위에 소속·이름·영문 이름·이능을 조판한 1200x600 카드를 만듭니다. 작성 규칙은 `references/image-prompt-and-assets.md` ⑤를 따릅니다.

```bash
uv run tools/images/name_card_cinematic.py <작품>/img --meta cards.json --out <작품>/img/명함
```

---

## 1. 표준 디렉터리 스캐폴딩

```bash
python3 deploy.py --scaffold --config <작품>/build/assets/prompts.json --root ~/내이미지폴더
```

실행 시 다음 구조가 자동으로 준비됩니다:
```
~/내이미지폴더/
  _배치표.md            전체 에셋 체크리스트
  <인물슬러그>/          인물 디렉터리 (README.md 가이드 포함)
  scene/                배경 및 장소 디렉터리
  mob/                  몬스터 및 위협 디렉터리
  event/                특수 이벤트 CG 디렉터리
```

제작용 범용 에셋 브라우저가 필요할 때만 `--asset-gallery`를 함께 붙입니다. 이 갤러리는
`prompts.json`에 있는 자산을 탐색하기 위한 도구이며, 작품 온보딩 사이트의 공개 범위를
결정하지 않습니다. 공개 소개 사이트는 `build/assets/showcase-brief.md`의 장부에서 허용한
정보만으로 별도 제작합니다.

```bash
python3 deploy.py --scaffold --asset-gallery --config <작품>/build/assets/prompts.json --root ~/내이미지폴더
```

---

## 2. WebP 고압축 일괄 변환

기존 `.png`, `.jpg` 이미지를 한 번에 고효율 `.webp`로 변환합니다:

```bash
python3 deploy.py --convert-webp --root ~/내이미지폴더
```

* PNG/JPEG 원본은 보존합니다. 같은 이름의 WebP가 이미 있거나 출력 경로가 충돌하면 중단합니다.
* 압축 결과의 용량과 시각 품질은 직접 확인합니다. 고정된 절감률이나 로딩 속도를 가정하지 않습니다.

---

## 3. 에셋 정합성 검사

```bash
python3 deploy.py --check --root ~/내이미지폴더
```

* `prompts.json`의 실제 인물·상황 키를 기준으로 검사합니다. 접두사만으로 등급을 정하지 않습니다. 일부 누락은 실패로 처리하지 않으므로 공개 목록을 별도로 대조합니다.

---

## 4. Cloudflare Pages 호스팅 배포

`deploy.py` 기본 실행은 GitHub+jsDelivr 이미지 배포이며 Pages 사이트 배포가 아닙니다. `--asset-gallery`는 제작용 범용 갤러리일 뿐 온보딩 사이트가 아닙니다. 작품 소개 사이트 제작·배포는 [호스팅·소개 사이트·배너 지침](../../references/hosting-showcase-and-banner.md)을 따릅니다. 아래는 개념적인 흐름이며 실제 배포 시 공식 문서에서 현재 절차를 확인합니다.

1. Cloudflare Dashboard ➡️ **Workers & Pages** ➡️ **Create application** ➡️ **Pages** 선택
2. GitHub 저장소 연동 또는 직접 `~/내이미지폴더` 업로드
3. 생성된 배포 URL (`https://<project-name>.pages.dev`)을 크랙 스토리챗 시스템 프롬프트의 `{IMG}` 매크로에 등록:
   ```text
   {IMG} = https://<project-name>.pages.dev
   ```
4. 크랙 프롬프트 내 호출:
   ```markdown
   ![]({IMG}/<인물슬러그>/<상황슬러그>.webp)
   ```


## 배경 크롭·장소명 배지

`crop_backgrounds.py`는 임의 크기 크롭, 장소명 배지, 이름 매칭 및 PNG/WebP 변환을 지원한다. Pillow 필요.

```bash
python3 tools/images/crop_backgrounds.py --src originals --out banners --size 1600x600 --anchor top --dry-run
python3 tools/images/crop_backgrounds.py --help
```

기본 배지를 빼려면 `--no-badge`, 글꼴 지정은 `--font`, 출력명 지정은 `--naming '{code}_{name}'`. 기존 출력은 `--overwrite` 없이는 변경하지 않는다. 원본 매칭이 모호하면 실패하며 명시적 `source`로 해결한다.

검증: `python3 -m unittest discover -s tools/images/tests -v`.
