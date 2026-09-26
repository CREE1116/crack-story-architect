# 7. 캐릭터 외형 디자인 지침 (Character Visual Design)

인물의 외형을 설계하고 `build/assets/characters.json` 프롬프트로 옮길 때 읽는다. 태그 문법·코드 규약은 [image-prompt-and-assets.md](image-prompt-and-assets.md)가 맡고, 이 문서는 **무엇을 어떤 순서로 정하고 어떻게 짧게 옮기는가**를 맡는다.

실제 제작에서 반복된 실패를 기준으로 정리했다: 캐스트 전원이 같은 회색 전술복을 입는다, 인물마다 따로 고른 원색이 한 화면에서 싸운다, 흑발이 여섯 명이다, 프롬프트가 1,000자를 넘어 그림체가 깨진다, 흰 셔츠+검은 조끼가 웨이터가 된다.

---

## 1. 작업 순서

```text
① 캐스트 표 → ② 세력 룩 → ③ 인물 컨셉 한 줄 → ④ 핵심 컬러 → ⑤ 헤어 → ⑥ 눈매·얼굴
→ ⑦ 체형 → ⑧ 의상·소품 → ⑨ 겹침 검사 → ⑩ 프롬프트 컴파일 → ⑪ UC → ⑫ 정본 동기화
```

인물 한 명씩 완성하지 않는다. **①~④는 캐스트 전체를 한 표에 놓고** 정한 뒤, 개별 인물로 내려간다. 한 명씩 만들면 각자는 그럴듯해도 모아 놓으면 색과 실루엣이 겹친다.

---

## 2. 캐스트 표와 세력 룩

### 캐스트 표
모든 인물을 한 표에 둔다. 칸이 비거나 두 인물이 같은 값이면 그 자리에서 고친다.

| # | 이름 | 세력 | 컨셉 한 줄 | 대표색 | 명도 | 헤어 실루엣 | 체형 | 시그니처 1 |
|---|---|---|---|---|---|---|---|---|
| 01 | 한서령 | 복구연합 | 기운 코트의 저항군 지휘관 | 슬레이트 네이비 | 어두움 | 비대칭 단발 | 곧은 슬림 | 은시계 |
| 06 | 백하진 | 개척동맹 | 탑을 가질 정복자 | 옥스블러드 | 강대비 | 초장 하이포니 | 모래시계 | 탑 모양 펜던트 |

**컨셉 한 줄**은 역할이 아니라 이미지다. "의료팀장"이 아니라 "사제복 같은 의료코트를 입은 전장의 간호장"처럼 옷차림이 떠오르게 쓴다.

### 세력 룩: 이념을 옷으로
세력이 둘 이상이면 **멀리서 봐도 편이 갈리게** 한다. 세력의 가치관을 옷의 규칙으로 번역한다.

| 가치관 | 옷의 규칙 | 예 |
|---|---|---|
| 공동체·규율 ('우리') | 공통 표식 하나 + 나머지는 역할 장비로만 개인차 | 제각각 주운 군용품이지만 **네이비 목스카프 + 흰 완장** |
| 개인·욕망 ('나') | 공통 표식 없음. 각자 **자기 소원을 몸에 두른다** | 탑을 원하는 자의 탑 모양 펜던트, 도시를 원하는 자의 아직 없는 도시의 열쇠 꾸러미 |
| 무소속·생존 | 제각각의 넝마, 직업 도구가 곧 정체성 | 정비공의 공구 하네스, 방송인의 드론 |

- **장르에 맞춘다.** 아포칼립스면 정규군보다 저항군이다. 새 제복·다림질보다 기운 옷, 짝 안 맞는 군용품이 맞다.
- **과장하지 않는다.** '개성 강함'을 징 박힌 가죽·전투 페인트·목 문신·체인 뭉치로 옮기면 망나니가 된다. 개성은 인물의 욕망에서 나온 소품 하나로 충분하다.

---

## 3. 핵심 컬러

### 세계 공통 팔레트부터
인물별로 색을 고르기 전에 **작품 전체가 쓸 12~16색**을 먼저 정한다. 모든 인물은 이 안에서만 고른다. 인물마다 따로 고른 원색이 부조화의 주원인이다.

아포칼립스 예시 (채도를 낮춘 색):

| 무채·어둠 | 차가움 | 흙빛 | 포인트 |
|---|---|---|---|
| ink black, charcoal, ash grey, bone white | slate navy, steel blue, muted teal, dusky plum | olive drab, khaki, sand beige | oxblood, muted rust, brass, dusty rose |

### 인물 한 명 = 인접색 한 묶음 (60-30-10)
- **60** 주색(겉옷) · **30** 보조색(안·하의) · **10** 강조색(소품·안감 한 곳).
- 한 인물 안의 고채도는 **한 곳**뿐이다. 둘 이상이 같은 무게로 튀면 시선이 갈 곳을 잃는다.
- **머리·눈은 대표색에서 한 단계 안**에서 고른다. 눈 색을 강조색과 맞추면 한 덩어리로 읽힌다(호박색 눈 ↔ 호박색 칼 술).
- 명도 인상(밝음·중간·어두움)을 인물마다 다르게 둔다. 흑백으로 봐도 구분돼야 한다.

### 캐스트 전체 규칙
- 같은 대표색 두 명 금지. 흑발은 **3명까지**, 스타일로 구분한다.
- 빨강 계열은 **한 명만 대표색**으로 쓰고, 나머지는 적십자·리본처럼 작은 점으로만 쓴다.
- 핑크 머리+노랑 재킷+청록 눈처럼 원색 셋을 한 인물에 두지 않는다. 필요하면 dusty rose·muted teal·bone white처럼 톤을 죽인다.

### 확인 방법
색을 글로만 정하지 않는다. `머리 / 눈 / 60 / 30 / 10` 다섯 칸짜리 견본표 이미지를 만들어 한 화면에서 본다. 줄 하나가 튀면 그 인물만 고친다. 견본표는 `build/assets` 밖에 둔다.

### 프롬프트의 색 이름
톤이 드러나는 이름을 쓴다: `muted slate navy`, `bone white`, `oxblood`, `dusty rose`, `brass`, `ash grey`, `ink black`. `blue`, `red`만 쓰면 원색이 나온다. UC에 `saturated colors, neon colors, vivid colors`를 둔다.

---

## 4. 헤어

**색 + 길이 + 형태(묶음·앞머리)** 셋을 반드시 함께 정한다. 헤어 실루엣은 인물 식별의 8할이다.

### 캐스트 안에서 겹치지 않게
헤어 실루엣을 아래 범주로 나누고, **같은 범주는 2명까지**. 흑발 단발이 셋이면 이미 겹친 것이다.

### 단부루 위키 검증 태그
`tools/images/search_tag.py`의 위키 DB에서 존재를 확인한 태그다(2026-09-26).

| 범주 | 태그 |
|---|---|
| 길이 | very short hair, short hair, medium hair, long hair, very long hair, absurdly long hair |
| 컷 | bob cut, inverted bob, hime cut, pixie cut, wolf cut, mullet, buzz cut, crew cut, undercut, sidecut, bowl cut, flipped hair, asymmetrical hair, shaved head, pompadour |
| 앞머리·옆머리 | blunt bangs, swept bangs, parted bangs, crossed bangs, curtained hair, choppy bangs, asymmetrical bangs, wispy bangs, flipped bangs, long bangs, short bangs, no bangs, bangs pinned back, hair between eyes, hair over one eye, hair over eyes, hair intakes, sidelocks, long sidelocks, single sidelock, asymmetrical sidelocks, low-tied sidelocks, forehead, widow's peak |
| 묶음 | ponytail, high ponytail, low ponytail, side ponytail, short ponytail, folded ponytail, braided ponytail, twintails, low twintails, short twintails, quad tails, one side up, two side up, half updo, updo, hair up, hair down, hair pulled back, hair slicked back, low-tied long hair, multi-tied hair, topknot |
| 번 | hair bun, double bun, single hair bun, braided bun, cone hair bun |
| 땋기 | braid, single braid, twin braids, low twin braids, side braid, side braids, long braid, french braid, crown braid, braided bangs, multiple braids, braided hair rings, hair rings, dreadlocks, cornrows |
| 결·질감 | straight hair, wavy hair, curly hair, messy hair, spiked hair, ringlets, drill hair, twin drills, big hair, afro, ahoge, heart ahoge, antenna hair, hair flaps, cowlick |
| 배색 | two-tone hair, streaked hair, colored inner hair, gradient hair, multicolored hair, split-color hair, colored tips |
| 위치 | hair over shoulder, hair behind ear, hair spread out, hair strand |
| 장식 | hairclip, hairpin, hair ornament, hair ribbon, hair tie, ponytail holder, scrunchie, hairband, headband, bandana, hair bobbles, hair beads, hair flower, hair stick, beret |

**위키가 없는 표현**(`low bun`, `messy bun`, `fluffy hair`, `windswept hair`, `layered hair`, `shaggy hair`, `jellyfish cut`, `dark roots`, `hair ring`)은 효과가 약하거나 무시될 수 있다. 위 표의 대안을 쓰거나, 꼭 필요하면 자연어 한 문장에 담는다.

---

## 5. 눈매·얼굴

- **눈 색 + 눈매 + 속눈썹·눈썹**을 한 묶음으로 둔다.
- 검증 태그:
  - 눈매: `tsurime`, `tareme`, `sanpaku`, `half-closed eyes`, `narrowed eyes`
  - 속눈썹·눈썹: `long eyelashes`, `thick eyelashes`, `eyeliner`, `thick eyebrows`, `short eyebrows`, `v-shaped eyebrows`
  - 동공: `slit pupils`, `heterochromia`
- 얼굴 개성 태그: `mole under eye`, `mole`, `freckles`, `scar on face`, `scar on cheek`, `scar on nose`, `scar across eye`, `bags under eyes`, `eyepatch`, `fang`, `tan`, `dark skin`, `pale skin`
- `round eyes`, `thin eyebrows`, `droopy eyes`, `hooded eyes`는 위키가 없다. 필요하면 문장으로 쓴다.
- `jitome`는 '반쯤 내리깐 경멸 눈'이라 표정처럼 굳는다. 기본 눈매로 쓰지 않는다.
- **표정을 넣지 않는다**(`calm`, `smile`, `confident`, `gentle`, `expressionless`). 표정은 감정 프리셋이 매 컷 얹는다. 베이스에 박으면 모든 컷이 같은 얼굴이 된다.
- **얼굴을 가리는 소품을 넣지 않는다**(입 가리는 스카프, 방독면 착용). 목에 걸거나 머리에 올린 상태로 둔다.

---

## 6. 체형

- **가슴·허리·골반·허벅지·다리**를 모두 정한다. 가슴 크기 태그는 필수다(그림체마다 체형이 흔들린다).
- 키·등신은 **정본(`characters.md`)에 적고** 프롬프트에는 넣지 않는다. 프롬프트에는 `tall female`, `petite` 정도만 둔다.
- 검증 태그:
  - 체격: `petite`, `tall female`, `skinny`, `curvy`, `muscular female`, `toned`, `abs`, `broad shoulders`, `biceps`, `collarbone`
  - 허리 아래: `narrow waist`, `wide hips`, `thick thighs`, `thigh gap`, `long legs`
  - 가슴: `flat chest`, `small breasts`, `medium breasts`, `large breasts`, `huge breasts`
  - 나이 인상: `mature female`
- `slender`, `athletic`, `hourglass figure`, `short stature`, `muscular arms`는 위키가 없다. `hourglass figure` 대신 `curvy, narrow waist, wide hips` 조합을 쓴다.
- **미형을 지킨다.** 주근깨·흉터·다크서클·기름때는 개성으로 둬도 된다. 뚱뚱해 보이거나 비율이 무너지는 것은 금지한다.
  - '평범한', '통통한', '서양배형', '짧은 다리', '앙상한', '땅딸막한' 같은 표현을 쓰지 않는다.
  - UC에 `fat, obese, chubby, plump, bad proportions, ugly, deformed face`를 둔다.

---

## 7. 의상·소품

- **세계관을 입힌다.** 아포칼립스면 해진 밑단, 덧댄 천, 덕트테이프, 기름 얼룩, 방독면, 수통, 붕대를 쓴다. 태그로 `patched clothes`, `torn clothes`, `dirty clothes`, `duct tape`, `dusty`를 붙이고, UC에 `pristine clothes, luxury`를 둔다.
- 세력이 다르면 낡은 정도도 달리한다. 규율 쪽은 기웠어도 가지런하고, 떠돌이는 너저분하다.
- **시그니처 소품은 1~2개.** 하나는 역할 장비(방패, 저격총, 드론), 하나는 욕망·과거의 흔적(언니의 탄피 목걸이, 탑 모양 펜던트)이다.
- **실루엣 훅 하나.** 멀리서 까맣게 칠해도 알아볼 형태를 둔다. 예: 망토처럼 걸친 코트, 등에 멘 방패, 키보다 긴 총, 설원 판초.
- 오해를 부르는 조합을 피한다.

| 조합 | 읽히는 것 |
|---|---|
| 흰 셔츠 + 검은 조끼 + 슬랙스 | 웨이터·집사 |
| 실크 블라우스 + 진주 목걸이 + 하이힐 | 백화점 쇼핑 |
| 징 박힌 가죽 + 전투 페인트 + 체인 | 약탈자 망나니 |
| 깨끗한 새 제복 + 다림질 | 정규군 (아포칼립스와 안 맞음) |

---

## 8. 프롬프트 컴파일 (`characters.json`)

### 형식
```json
[
  {"name": "한서령", "prompt": "...", "uc": "..."}
]
```
키는 `name`, `prompt`, `uc` 셋뿐이다. 한 줄에 한 명씩 쓴다.

### 규칙
1. **길이 300~450자.** 길면 캐릭터 태그가 스타일 태그를 밀어내 그림체가 깨진다.
2. **순서**: `1girl, solo` (+`mature female`) → `1.3::헤어::` → `1.3::눈::` → 체형 태그 → 의상·소품 태그 → 자연어 문장.
3. **가중치는 헤어·눈 두 곳만** 1.3. 체형·의상까지 묶으면 서로 밀어낸다.
4. **자연어는 인물당 1문장**(많아도 2). 태그로 안 되는 **대표색 결속**에만 쓴다.
   - 대문자로 시작하고 `.,`로 끝낸다. 마지막 문장도 `.,`로 닫는다.
   - 문장 안에 쉼표를 넣지 않는다(태그로 쪼개진다).
   - 예: `A patched slate navy officer coat over mismatched surplus gear with a navy neck scarf and a white armband.,`
5. **넣지 않는다**: 표정, 배경·장소, 구도, 나이 숫자(`31yo`), 키(`170cm`), 직업명(`faction leader`), 얼굴 가리는 소품.

### 완성 예
```text
1girl, solo, 1.3::black hair, long hair, straight hair, hime cut::, 1.3::purple eyes, tsurime, long eyelashes::, tall female, medium breasts, long legs, fur collar, long coat, turtleneck, tinted eyewear, eyewear on head, fingerless gloves, leather boots, pearl earrings, keyring, A charcoal fur-collared coat hung with a ring of old brass keys and a blueprint tube on her back.,
```

---

## 9. UC

순서대로 쌓는다.

1. **품질·미성년**: `loli, child, kid, chibi, super deformed, lowres, bad anatomy, bad hands, extra digits, fewer digits, worst quality, low quality, signature, watermark`
2. **미형**: `ugly, deformed face, bad proportions, fat, obese, chubby, plump`
3. **색**: `saturated colors, neon colors, vivid colors`
4. **세계관**: `pristine clothes, luxury` (정갈한 인물이면 `clean uniform`)
5. **인물의 반대 속성**: 헤어(단발이면 `long hair, ponytail`), 체형(슬림이면 `huge breasts`), 의상(`skirt, dress`), 이전에 잘못 나왔던 것(웨이터가 나왔으면 `white shirt, vest, waiter`)
6. **다른 세력의 표식**: 개척동맹 인물이면 `military uniform, armband`, 복구연합 인물이면 `facepaint, spikes`

**넣지 않는다**: `smile`처럼 표정 태그. 감정 프리셋의 웃음 컷이 막힌다.

**헤어나 의상을 바꾸면 UC도 다시 본다.** 트윈테일로 바꿨는데 UC에 `twintails`가 남아 있는 경우가 흔하다.

---

## 10. 정본 동기화

외형을 바꾸면 아래를 **한 번에** 고친다. 하나라도 빠지면 연기와 이미지가 어긋난다.

| 위치 | 내용 |
|---|---|
| `characters.md` `- 외형:` | 키·등신·헤어·눈·의상·시그니처(한국어 정본) |
| `story.md` 세력 항목 | 세력 룩 규칙 한 줄 |
| 통합 프롬프트 인물 명부 | 외형 칸(짧게) |
| 키워드북 인물 항목 | 키·외형 칸 |
| `characters.json` | 프롬프트·UC |

---

## 11. 검수 체크리스트

- [ ] 캐스트 표에 빈칸·중복이 없다(대표색, 헤어 실루엣, 시그니처)
- [ ] 견본표 이미지에서 튀는 줄이 없다
- [ ] 흑발 3명 이하, 빨강 대표색 1명
- [ ] 세력이 멀리서 갈린다(공통 표식 vs 개인 소품)
- [ ] 오해 조합(웨이터·백화점·망나니)이 없다
- [ ] 프롬프트 300~450자, 가중치 2곳, 문장 1~2개 `.,`
- [ ] 표정·배경·숫자·직업명 없음
- [ ] 위키 없는 태그를 핵심 자리에 쓰지 않았다
- [ ] UC에 표정 태그 없음, 새 헤어·의상과 충돌 없음
- [ ] 정본·명부·키워드북 외형이 같다
- [ ] `scripts/checks/check_character_prompts.py`가 통과한다
- [ ] 실제로 한두 명 생성해 봤다(정적 검사 통과 ≠ 그림이 잘 나옴)
