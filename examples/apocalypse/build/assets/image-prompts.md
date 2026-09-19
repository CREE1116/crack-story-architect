# Image Prompts Sheet (Danbooru Tag Based)

> 모든 태그는 `tools/images/search_tag.py`로 단부루 위키에서 실재를 확인한 공식 태그다.
> 베이스 프롬프트는 고정 앵커이고, 상황별로 태그를 가감(+a / -소거)해서 변주한다.

## 1. Banner & Thumbnail
- **Banner (16:9)**: masterpiece, best quality, ultra-detailed, no humans, scenery, wide shot, cinematic lighting, ruined city, overcast sky, volumetric light
- **Thumbnail (1:1)**: masterpiece, best quality, ultra-detailed, 1girl, solo, upper body, looking at viewer, cinematic lighting

## 2. 서린 (seorin)
- **Base Anchor**: 1girl, solo, 1.35::burn scar on left collarbone::, 1.35::black hair, low ponytail::, 1.35::red eyes, tsurime::, 1.3::slender athletic build::, 1.35::black tactical turtleneck, grey military jacket, charcoal cargo pants, combat boots::
- **Tag Mutability**:
  - 전투/손상 (+a): `torn clothes, blood on cheek, disheveled hair, dynamic combat stance`
  - 휴식/일상 (-소거·대체): 군용 재킷 소거 ➔ `tank top, towel around neck`
  - 글리치 가드 (-소거): 밀착 구도에서는 `tactical rifle`, `earpiece` 태그를 일시 제외한다.

## 3. 쿠로하 (kuroha)
- **Base Anchor**: 1girl, solo, 1.35::exposed cybernetic left arm, glowing blue joints::, 1.35::silver hair, short hair, undercut::, 1.35::grey eyes, half-closed eyes::, 1.3::slender::, 1.35::black rider jacket, red inner shirt, dark jeans::
- **Tag Mutability**:
  - 이능 발동 (+a): `glowing red joints, heat haze, sparks`
  - 정비 중 (-소거·대체): 라이더 재킷 소거 ➔ `sleeveless shirt, mechanical parts on table`
  - 글리치 가드 (-소거): 포옹·밀착 구도에서는 `rider jacket` 어깨 장식 태그를 제외한다.

## 4. 배경 (scenes / backgrounds)
- **sc01**: masterpiece, best quality, 1.2::no humans::, scenery, exterior, ruined apartment complex, overgrown playground, rusted swings, crows, grey sky
- **sc02**: masterpiece, best quality, 1.2::no humans::, scenery, exterior, ruined shopping district, broken shop windows, flickering neon signs, wet asphalt
- **sc03**: masterpiece, best quality, 1.2::no humans::, scenery, exterior, skyscraper ruins, stopped ferris wheel, glowing rift in the sky, heavy fog
- **bg01**: masterpiece, best quality, 1.2::no humans::, scenery, interior, underground tunnel, flickering lights, cargo crates, pipes

> 배경은 `crop_backgrounds.py`로 1024x400 WebP로 규격화한 뒤 CDN에 올린다.
