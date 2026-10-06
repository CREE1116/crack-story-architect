#!/usr/bin/env python3
"""Crack Character Chat Playwright Automation Sync Tool.

Directly reverse-engineered and verified against the actual Crack Character Editor DOM:
- Step 1 (profile): '캐릭터 설정'
    - Name: input[placeholder*='사용자는 당신의 캐릭터를 이렇게 부를 거예요'] (<= 30자)
    - Simple Description: textarea[placeholder*='어떤 캐릭터인지 설명할 수 있는 간단한 소개'] (<= 30자)
    - Image: input[type='file']
- Step 2 (intro): '인트로 및 예시 대화'
    - Play Guide: textarea[placeholder*='사용자를 위한 가이드를 작성해주세요'] (<= 500자)
    - Intro Setup: button:has-text('인트로 설정') -> Chat UI (User <= 150자, Character <= 150자)
    - Example Messages: button:has-text('예시 대화 추가') (up to 10 sets, each <= 150자)
- Step 3 (prompt): '프롬프트'
    - System Prompt: textarea[placeholder*='인트로와 예시 대화를 설정하면 적절한 프롬프트를 작성해 드려요'] (<= 2,000자)
- Step 4 (advance): '고급 기능'
    - Situation Images: situation images upload & keyword mapping (up to 50)
- Step 5 (info): '캐릭터 상세'
    - Detail Description: textarea[placeholder*='캐릭터의 성격이나 서사'] (<= 1,000자)
    - Genre: Select Radix dropdown ('장르를 선택해주세요')
    - Target: Select Radix dropdown ('타겟을 선택해주세요' -> 남성향 / 여성향 / 전체)
    - Hashtags: input[placeholder*='단어 입력 후 엔터'] (up to 10 tags)

Directory convention:
    <story-project>/char_chat/<character_name>/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_DIR = Path.home() / ".crack" / "profile"
DEFAULT_LOGIN_URL = "https://crack.wrtn.ai"

NAME_MAX = 30
TAGLINE_MAX = 30
PROMPT_MAX = 2000
PLAY_GUIDE_MAX = 500
CHARACTER_DESC_MAX = 1000
DIALOGUE_MAX = 150
MAX_EXAMPLES = 10
HASHTAG_MAX = 10


def crack_len(text: str) -> int:
    """UTF-16 surrogate-pair aware length matching Crack platform."""
    if not text:
        return 0
    return max(len(text), len(text.encode("utf-16-le")) // 2)


@dataclass
class DialogueUtterance:
    role: str  # 'user' | 'character'
    text: str


@dataclass
class CharacterArtifacts:
    project_dir: Path
    name: str
    tagline: str
    prompt: str
    play_guide: str
    character_desc: str
    intro_background: str = ""
    intro: list[DialogueUtterance] = field(default_factory=list)
    examples: list[list[DialogueUtterance]] = field(default_factory=list)
    genre: str = "일상"
    target: str = "전체"
    hashtags: list[str] = field(default_factory=list)
    thumbnail_path: Path | None = None
    situation_image_path: Path | None = None


def parse_dialogue_utterances(body: str) -> list[DialogueUtterance]:
    """Parse dialogue lines preserving sequence of character and user utterances."""
    messages = []
    for line in body.splitlines():
        line = line.strip()
        m_char = re.match(r"^-\s*\*\*(?:캐릭터|인물|assistant)\*\*\s*:\s*(.+)$", line, re.I)
        m_user = re.match(r"^-\s*\*\*(?:유저|사용자|user)\*\*\s*:\s*(.+)$", line, re.I)
        if m_char:
            messages.append(DialogueUtterance(role="character", text=m_char.group(1).strip()))
        elif m_user:
            messages.append(DialogueUtterance(role="user", text=m_user.group(1).strip()))
    return messages


def load_character_artifacts(char_dir: Path) -> CharacterArtifacts:
    char_dir = char_dir.resolve()
    if not char_dir.exists():
        raise FileNotFoundError(f"캐릭터 디렉터리를 찾을 수 없습니다: {char_dir}")

    build_dir = char_dir / "build"
    name = ""
    tagline = ""
    genre = "일상"
    target = "전체"
    hashtags: list[str] = []

    # Meta
    meta_json = build_dir / "meta.json"
    meta_yaml = char_dir / "meta.yaml"
    if meta_json.exists():
        d = json.loads(meta_json.read_text(encoding="utf-8"))
        name = d.get("name", "")
        tagline = d.get("tagline", "")
        genre = d.get("genre", "일상")
        target = d.get("target", "전체")
        hashtags = d.get("hashtags", [])
    elif meta_yaml.exists():
        raw = meta_yaml.read_text(encoding="utf-8")
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("tagline:"):
                tagline = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("genre:"):
                genre = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("target:"):
                target = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("-") and "#" in line:
                hashtags.append(line.lstrip("- ").strip().strip("\"'"))

    if not name:
        name = char_dir.name

    # Prompt
    prompt = ""
    prompt_path = build_dir / "prompt.md"
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    elif (char_dir / "character.md").exists():
        prompt = (char_dir / "character.md").read_text(encoding="utf-8").strip()

    # Play Guide
    play_guide = ""
    guide_path = build_dir / "play-guide.md"
    if guide_path.exists():
        play_guide = guide_path.read_text(encoding="utf-8").strip()
    elif (char_dir / "guide.md").exists():
        m = re.search(r"##\s*플레이가이드[^\n]*\n(.*?)(?=\n##|\Z)", (char_dir / "guide.md").read_text(encoding="utf-8"), re.S)
        if m:
            play_guide = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip()

    # Character Description
    char_desc = ""
    desc_path = build_dir / "character-desc.md"
    if desc_path.exists():
        char_desc = desc_path.read_text(encoding="utf-8").strip()
    elif (char_dir / "guide.md").exists():
        m = re.search(r"##\s*캐릭터 설명[^\n]*\n(.*?)(?=\n##|\Z)", (char_dir / "guide.md").read_text(encoding="utf-8"), re.S)
        if m:
            char_desc = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip()

    # Dialogues (Multi-utterance sequence & Situation Background)
    intro_bg = ""
    intro: list[DialogueUtterance] = []
    examples: list[list[DialogueUtterance]] = []

    if (char_dir / "dialogues.md").exists():
        content = (char_dir / "dialogues.md").read_text(encoding="utf-8")
        sections = re.split(r"(?m)^##\s+", content)
        for sec in sections:
            if not sec.strip():
                continue
            lines = sec.strip().splitlines()
            hdr = lines[0].lower()
            body = "\n".join(lines[1:])
            if ("상황 배경" in hdr or "시작 프롬프트" in hdr or "intro_bg" in hdr or "intro background" in hdr or ("배경" in hdr and "예시" not in hdr)) and "예시" not in hdr:
                cleaned = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
                cleaned = re.sub(r"(?m)^---+\s*$", "", cleaned).strip()
                intro_bg = cleaned
            else:
                msgs = parse_dialogue_utterances(body)
                if not msgs:
                    continue
                if "인트로" in hdr:
                    intro = msgs
                elif "예시" in hdr or "대화" in hdr:
                    examples.append(msgs)

    if not intro_bg and (build_dir / "intro-background.md").exists():
        intro_bg = (build_dir / "intro-background.md").read_text(encoding="utf-8").strip()

    # Fallback to json if exists
    if not intro and (build_dir / "intro.json").exists():
        try:
            d = json.loads((build_dir / "intro.json").read_text(encoding="utf-8"))
            if isinstance(d, list):
                intro = [DialogueUtterance(role=m.get("role", "user"), text=m.get("text", "")) for m in d]
            elif isinstance(d, dict):
                if d.get("user"):
                    intro.append(DialogueUtterance(role="user", text=d["user"]))
                if d.get("character"):
                    intro.append(DialogueUtterance(role="character", text=d["character"]))
        except Exception:
            pass

    # Images
    thumb: Path | None = None
    for ext in ("png", "webp", "jpg", "jpeg"):
        p = char_dir / "assets" / f"thumbnail.{ext}"
        if p.exists():
            thumb = p
            break
        p_story = char_dir.parent.parent / "assets" / f"thumbnail.{ext}"
        if p_story.exists() and not thumb:
            thumb = p_story

    sit_img: Path | None = None
    for ext in ("png", "webp", "jpg", "jpeg"):
        p = char_dir / "assets" / f"situation.{ext}"
        if p.exists():
            sit_img = p
            break

    return CharacterArtifacts(
        project_dir=char_dir,
        name=name,
        tagline=tagline,
        prompt=prompt,
        play_guide=play_guide,
        character_desc=char_desc,
        intro_background=intro_bg,
        intro=intro,
        examples=examples[:MAX_EXAMPLES],
        genre=genre,
        target=target,
        hashtags=hashtags[:HASHTAG_MAX],
        thumbnail_path=thumb,
        situation_image_path=sit_img,
    )


def run_inspect(char_dir: Path) -> int:
    art = load_character_artifacts(char_dir)
    print(f"\n=======================================================")
    print(f"📊 [캐릭터챗 프리뷰: {art.name}] ({char_dir})")
    print(f"=======================================================")
    print(f"- 캐릭터 이름 (최대 30자): [{crack_len(art.name)}자] {art.name}")
    print(f"- 한 줄 소개 (최대 30자): [{crack_len(art.tagline)}자] {art.tagline}")
    print(f"- 장르 / 타겟: {art.genre} / {art.target}")
    print(f"- 해시태그: {', '.join(art.hashtags) if art.hashtags else '(없음)'}")
    print(f"- 썸네일 이미지: {art.thumbnail_path.name if art.thumbnail_path else '⚠️ 없음'}")
    print(f"- 상황 이미지: {art.situation_image_path.name if art.situation_image_path else 'ℹ️ 선택사항'}")
    print(f"- 상황 배경 / 시작 프롬프트 (최대 500자): {crack_len(art.intro_background)}자")
    print(f"- 플레이 가이드 (최대 500자): {crack_len(art.play_guide)}자")
    print(f"- 시스템 프롬프트 (최대 2,000자): {crack_len(art.prompt)}자")
    print(f"- 캐릭터 설명 (최대 1,000자): {crack_len(art.character_desc)}자")
    print(f"- 인트로 대화: {len(art.intro)}개 발화")
    for utt in art.intro:
        print(f"   * [{utt.role}] ({crack_len(utt.text)}자) {utt.text[:40]}...")
    print(f"- 예시 대화 세트: {len(art.examples)}개 (최대 10개)")
    for i, ex in enumerate(art.examples, 1):
        print(f"   [{i}] {len(ex)}개 발화")
        for utt in ex:
            print(f"       * [{utt.role}] ({crack_len(utt.text)}자) {utt.text[:35]}...")
    print(f"=======================================================\n")
    return 0


def fill_react_input(page: Any, selector_or_locator: Any, value: str) -> bool:
    """Safely fill text into React-controlled input/textarea and dispatch events."""
    try:
        if isinstance(selector_or_locator, str):
            loc = page.locator(selector_or_locator).first
        else:
            loc = selector_or_locator
        if loc.count() > 0:
            loc.scroll_into_view_if_needed(timeout=2000)
            loc.click(timeout=2000)
            loc.fill(value, timeout=3000)
            return True
    except Exception:
        pass

    try:
        page.evaluate(
            """
            ([sel, val]) => {
                let el = typeof sel === 'string' ? document.querySelector(sel) : sel;
                if (el) {
                    el.focus();
                    if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, "value"
                        )?.set || Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, "value"
                        )?.set;
                        if (nativeInputValueSetter) {
                            nativeInputValueSetter.call(el, val);
                        } else {
                            el.value = val;
                        }
                    }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.blur();
                }
            }
            """,
            [selector_or_locator if isinstance(selector_or_locator, str) else None, value]
        )
        return True
    except Exception:
        return False


def switch_step_tab(page: Any, step_id: str, label_fallback: str) -> bool:
    """Switch character builder steps (profile, intro, prompt, advance, info)."""
    loc = page.locator(f"a[href*='step={step_id}'], a[id*='trigger-{step_id}'], button:visible:has-text('{label_fallback}')")
    if loc.count() > 0:
        try:
            loc.first.click()
            time.sleep(1.2)
            return True
        except Exception:
            pass
    return False


def navigate_to_create_character(page: Any) -> bool:
    """Navigate from Crack home to '내 작품' -> '작품 만들기' -> '캐릭터'."""
    print("\n🧭 [캐릭터 에디터 진입 탐색 시작]")

    # Check if already in character builder
    if "builder/character" in page.url:
        print("   ✅ 이미 캐릭터 에디터 화면에 진입되어 있습니다.")
        return True

    # 1. '내 작품' 메뉴 클릭
    my_works = page.locator(
        "button:visible:has-text('내 작품'), a:visible:has-text('내 작품'), div[role='tab']:visible:has-text('내 작품'), span:visible:has-text('내 작품')"
    )
    if my_works.count() > 0:
        try:
            my_works.first.click()
            time.sleep(1.5)
            print("   ✅ '내 작품' 메뉴 클릭 완료")
        except Exception:
            pass

    # 2. '작품 만들기' 버튼 클릭
    create_btn = page.locator(
        "button:visible:has-text('작품 만들기'), a:visible:has-text('작품 만들기'), button:visible:has-text('새 작품')"
    )
    if create_btn.count() > 0:
        try:
            create_btn.first.click()
            time.sleep(1.5)
            print("   ✅ '작품 만들기' 버튼 클릭 완료")
        except Exception as e:
            print(f"   ⚠️ '작품 만들기' 클릭 실패: {e}")

    # 3. '캐릭터' 모달/카드 선택
    print("   🔍 3단계: '캐릭터' 타입 선택 중...")
    char_btn = page.locator(
        "button:visible:has-text('캐릭터'), div[role='button']:visible:has-text('캐릭터'), p:visible:has-text('캐릭터'), h3:visible:has-text('캐릭터')"
    )
    if char_btn.count() > 0:
        try:
            for idx in range(char_btn.count()):
                el = char_btn.nth(idx)
                txt = el.inner_text().strip()
                if "캐릭터" in txt and len(txt) < 20:
                    el.click(timeout=2000)
                    time.sleep(2.5)
                    print("   ✅ '캐릭터' 타입 선택 완료 -> 에디터 진입!")
                    return True
        except Exception:
            pass

    return True


def send_speech_bubble(page: Any, role: str, text: str, char_name: str) -> bool:
    """Send a dialogue speech bubble by explicitly clicking the role toggle button ('사용자' vs '[캐릭터이름]')."""
    if not text:
        return False

    clean_text = text.strip()[:DIALOGUE_MAX]

    # 1. 화자 선택 칩 버튼 명시적 클릭 ('사용자' vs 캐릭터 이름)
    if role == "user":
        user_btn = page.locator("button:visible:has-text('사용자')").first
        if user_btn.count() > 0:
            try:
                user_btn.click()
                time.sleep(0.3)
            except Exception:
                pass
    else:  # character / assistant
        char_name_clean = char_name[:10] if char_name else ""
        char_btn = page.locator(
            f"button:visible:has-text('{char_name_clean}'), button:visible:has-text('캐릭터 이름')"
        ).first
        if char_btn.count() > 0:
            try:
                char_btn.click()
                time.sleep(0.3)
            except Exception:
                pass

    # 2. 텍스트 입력창 클릭 및 값 입력 후 전송
    chat_input = page.locator("textarea[placeholder*='대사를 입력해 주세요']").first
    if chat_input.count() > 0:
        try:
            chat_input.click()
            chat_input.fill("")
            chat_input.fill(clean_text)
            time.sleep(0.3)
            page.keyboard.press("Enter")
            time.sleep(0.5)

            # Enter로 전송이 안 되고 텍스트가 남아있는 경우 send 버튼 클릭
            try:
                if chat_input.input_value().strip():
                    send_btn = page.locator("button.rounded-full:visible").last
                    if send_btn.count() > 0:
                        send_btn.click()
                        time.sleep(0.5)
            except Exception:
                pass

            return True
        except Exception as e:
            print(f"      ⚠️ 발화 전송 실패: {e}")
            return False
    return False


def inject_character_all(page: Any, art: CharacterArtifacts) -> bool:
    print(f"\n🚀 [캐릭터챗 데이터 정밀 주입 시작: {art.name}]")

    # =========================================================================
    # Step 1: 캐릭터 설정 (profile)
    # =========================================================================
    print("\n[Step 1] 캐릭터 설정 (profile) 주입...")
    switch_step_tab(page, "profile", "캐릭터 설정")

    # Name: input[placeholder*='사용자는 당신의 캐릭터를 이렇게 부를 거예요']
    name_input = page.locator("input[placeholder*='사용자는 당신의 캐릭터를 이렇게 부를 거예요']").first
    if name_input.count() > 0:
        fill_react_input(page, name_input, art.name[:NAME_MAX])
        print(f"   - 캐릭터 이름: {art.name[:NAME_MAX]}")
    else:
        # fallback
        name_input_fb = page.locator("input[placeholder*='이름']").first
        if name_input_fb.count() > 0:
            fill_react_input(page, name_input_fb, art.name[:NAME_MAX])
            print(f"   - 캐릭터 이름(fallback): {art.name[:NAME_MAX]}")

    # Tagline: textarea or input[placeholder*='어떤 캐릭터인지 설명할 수 있는 간단한 소개']
    tagline_input = page.locator(
        "textarea[placeholder*='어떤 캐릭터인지 설명할 수 있는 간단한 소개'], input[placeholder*='어떤 캐릭터인지 설명할 수 있는 간단한 소개']"
    ).first
    if tagline_input.count() > 0:
        fill_react_input(page, tagline_input, art.tagline[:TAGLINE_MAX])
        print(f"   - 한 줄 소개: {art.tagline[:TAGLINE_MAX]}")

    # Thumbnail Upload
    if art.thumbnail_path and art.thumbnail_path.exists():
        file_inputs = page.locator("input[type='file']")
        if file_inputs.count() > 0:
            try:
                file_inputs.first.set_input_files(str(art.thumbnail_path))
                print(f"   - 대표 이미지 업로드: {art.thumbnail_path.name}")
                # 이미지 업로드 후 나타나는 크롭 모달의 [자르기] 버튼 클릭
                time.sleep(1.5)
                crop_btn = page.locator("button:visible:has-text('자르기'), button:visible:has-text('확인'), button:visible:has-text('적용')")
                if crop_btn.count() > 0:
                    try:
                        crop_btn.first.click(timeout=3000)
                        time.sleep(2.0)
                        print("   - 이미지 크롭 [자르기] 버튼 클릭 완료")
                    except Exception as e:
                        print(f"   ⚠️ 자르기 버튼 클릭 실패: {e}")
            except Exception as e:
                print(f"   ⚠️ 대표 이미지 업로드 실패: {e}")

    # 현재 화면 버튼 덤프
    try:
        btns = [page.locator('button:visible').nth(i).inner_text().strip().replace('\n', ' ') for i in range(page.locator('button:visible').count())]
        print(f"   🔍 크롭 후 보이는 버튼: {btns}")
    except Exception:
        pass

    # Step 1 완료 후 [다음] 클릭하여 레코드 발급 및 Step 2 이동
    nxt_1 = page.locator("button:visible:has-text('다음')").first
    if nxt_1.count() > 0:
        try:
            nxt_1.click(timeout=3000)
            time.sleep(2.5)
            print("   ✅ [다음] 버튼 클릭 -> Step 2(intro) 이동")
        except Exception as e:
            print(f"   ℹ️ [다음] 버튼 클릭 대기 초과 또는 불가: {e}")
            switch_step_tab(page, "intro", "인트로")
    else:
        switch_step_tab(page, "intro", "인트로")

    # =========================================================================
    # Step 2: 인트로 및 예시 대화 (intro)
    # =========================================================================
    print("\n[Step 2] 인트로 및 예시 대화 (intro) 주입...")
    time.sleep(1.0)

    # 1. 상황 배경 (시작 프롬프트: introBackground, 최대 500자)
    # 인트로 설정 버튼을 누르기 전, Step 2 메인 화면에 위치한 연필 버튼을 직접 클릭합니다.
    # 사용자가 제공한 DOM: <div class="css-5ax1kt e1pfv5720"><button ...><svg><path d="m17.44 1.9..."/></svg></button></div>
    if art.intro_background:
        print(f"   - 상황 배경 (시작 프롬프트) 주입: {crack_len(art.intro_background)}자")
        try:
            # Step 2 메인 화면의 상황 배경 연필 수정 아이콘 탐색
            # 사용자가 전달한 DOM 구조: <div class="css-5ax1kt e1pfv5720"><button ...><svg><path d="m17.44 1.9..."/></svg></button></div>
            pencil_selectors = [
                "button:visible:has(path[d*='m17.44 1.9']):not(:has-text('인트로'))",
                "button:visible:has(path[d*='M17.44 1.9']):not(:has-text('인트로'))",
                "div.css-5ax1kt button:visible",
                "div[class*='css-5ax1kt'] button:visible",
                "div[class*='e1pfv5720'] button:visible",
            ]
            
            pencil_clicked = False
            for sel in pencil_selectors:
                btns = page.locator(sel)
                if btns.count() > 0:
                    for b_idx in range(btns.count()):
                        btn = btns.nth(b_idx)
                        txt = (btn.inner_text() or "").strip()
                        # '인트로 설정' 버튼이나 다른 대형 버튼은 제외
                        if "인트로" in txt:
                            continue
                        btn.scroll_into_view_if_needed()
                        btn.click()
                        time.sleep(1.0)
                        pencil_clicked = True
                        print(f"   ✅ 상황 배경 연필 버튼 클릭 완료 (selector: {sel}, idx: {b_idx})")
                        break
                    if pencil_clicked:
                        break

            if not pencil_clicked:
                # Fallback: 상황 배경 안내 문구 영역 클릭 시도
                hint_box = page.locator("*:has-text('사용자에게는 보이지 않지만')").last
                if hint_box.count() > 0:
                    hint_box.scroll_into_view_if_needed()
                    hint_box.click()
                    time.sleep(1.0)
                    print("   ℹ️ 상황 배경 안내 박스 직접 클릭 완료")

            # 수정 모드 textarea 탐색 (placeholder 매칭 및 일반 textarea 탐색)
            bg_ta = page.locator("textarea[placeholder*='사용자에게는 보이지 않지만']").first
            if bg_ta.count() == 0:
                # 열려있는 첫 번째 비어있거나 상황배경용 textarea
                all_tas = page.locator("textarea:visible")
                for i in range(all_tas.count()):
                    t = all_tas.nth(i)
                    ph = t.get_attribute("placeholder") or ""
                    if "가이드" not in ph and "대사" not in ph:
                        bg_ta = t
                        break

            if bg_ta.count() > 0:
                bg_ta.fill("")
                bg_ta.fill(art.intro_background[:PLAY_GUIDE_MAX])
                time.sleep(0.5)
                
                # '수정 완료' 또는 '완료' 버튼 클릭
                done_btn = page.locator("button:visible:has-text('수정 완료'), button:visible:has-text('완료')").first
                if done_btn.count() > 0:
                    done_btn.click()
                    time.sleep(0.8)
                    print("   ✅ 상황 배경 '수정 완료' 저장 성공!")
                else:
                    page.keyboard.press("Enter")
                    time.sleep(0.5)
                    print("   ✅ 상황 배경 Enter 저장 시도")
                
                # 저장 확인
                page_text = page.locator("body").inner_text()
                if art.intro_background[:20] in page_text:
                    print(f"   ✨ 상황 배경 화면 반영 확인 성공: '{art.intro_background[:20]}...'")
                else:
                    print(f"   ℹ️ 상황 배경 반영 상태 (화면 텍스트 검증 진행)")
            else:
                print("   ⚠️ 상황 배경 입력 textarea를 찾지 못했습니다.")
        except Exception as e:
            print(f"   ⚠️ 상황 배경 주입 중 에러: {e}")

    # 2. Play Guide: textarea[placeholder*='사용자를 위한 가이드를 작성해주세요']
    guide_ta = page.locator("textarea[placeholder*='사용자를 위한 가이드를 작성해주세요']").first
    if guide_ta.count() > 0 and art.play_guide:
        fill_react_input(page, guide_ta, art.play_guide[:PLAY_GUIDE_MAX])
        print(f"   - 플레이 가이드: {crack_len(art.play_guide[:PLAY_GUIDE_MAX])}자")

    # 3. Intro Setup: button:has-text('인트로 설정')
    intro_btn = page.locator("button:visible:has-text('인트로 설정')").first
    if intro_btn.count() > 0 and art.intro:
        try:
            intro_btn.click()
            time.sleep(1.2)
            print(f"   - 인트로 대화 패널 열기 완료 ({len(art.intro)}개 발화 전송)")
            for idx, utt in enumerate(art.intro, 1):
                success = send_speech_bubble(page, utt.role, utt.text, art.name)
                print(f"      * [{idx}/{len(art.intro)}] {utt.role}: {utt.text[:30]}... ({'성공' if success else '실패'})")
                time.sleep(0.4)
            print("   - 인트로 대화 주입 완료")
        except Exception as e:
            print(f"   ⚠️ 인트로 대화 주입 실패: {e}")

    # 3. Example messages: button:has-text('예시 대화 추가')
    if art.examples:
        print(f"   - 예시 대화 세트 {len(art.examples)}개 주입 (화자 전환 적용)...")
        for set_idx, ex_utterances in enumerate(art.examples, 1):
            try:
                # Check if '예시 {set_idx}' already exists
                ex_chip = page.locator(f"button:visible:has-text('예시 {set_idx}')").first
                if ex_chip.count() == 0:
                    add_ex_btn = page.locator("button:visible:has-text('예시 대화 추가')")
                    if add_ex_btn.count() > 0:
                        add_ex_btn.first.click()
                        time.sleep(1.0)
                        ex_chip = page.locator(f"button:visible:has-text('예시 {set_idx}')").first

                if ex_chip.count() > 0:
                    ex_chip.click()
                    time.sleep(1.0)
                    print(f"      * [예시 {set_idx}] 패널 활성화 성공 ({len(ex_utterances)}개 발화 전송)")
                    for u_idx, utt in enumerate(ex_utterances, 1):
                        success = send_speech_bubble(page, utt.role, utt.text, art.name)
                        print(f"         - ({u_idx}/{len(ex_utterances)}) {utt.role}: {utt.text[:25]}... ({'성공' if success else '실패'})")
                        time.sleep(0.4)
                else:
                    print(f"      ⚠️ [예시 {set_idx}] 버튼을 찾을 수 없음")
            except Exception as e:
                print(f"      ⚠️ 예시 {set_idx} 주입 실패: {e}")

    # Step 2 완료 후 [다음] 클릭
    nxt_2 = page.locator("button:visible:has-text('다음')").first
    if nxt_2.count() > 0:
        try:
            nxt_2.click()
            time.sleep(2.0)
            print("   ✅ [다음] 버튼 클릭 -> Step 3(prompt) 이동")
        except Exception:
            switch_step_tab(page, "prompt", "프롬프트")
    else:
        switch_step_tab(page, "prompt", "프롬프트")

    # =========================================================================
    # Step 3: 프롬프트 (prompt)
    # =========================================================================
    print("\n[Step 3] 프롬프트 (prompt) 주입...")
    time.sleep(1.0)
    prompt_ta = page.locator(
        "textarea[placeholder*='인트로와 예시 대화를 설정하면'], textarea[placeholder*='프롬프트']"
    ).first
    if prompt_ta.count() > 0:
        fill_react_input(page, prompt_ta, art.prompt[:PROMPT_MAX])
        print(f"   - 캐릭터 시스템 프롬프트: {crack_len(art.prompt[:PROMPT_MAX])}자")

    # Step 3 완료 후 [다음] 클릭
    nxt_3 = page.locator("button:visible:has-text('다음')").first
    if nxt_3.count() > 0:
        try:
            nxt_3.click()
            time.sleep(2.0)
            print("   ✅ [다음] 버튼 클릭 -> Step 4(advance) 이동")
        except Exception:
            switch_step_tab(page, "advance", "고급 기능")
    else:
        switch_step_tab(page, "advance", "고급 기능")

    # =========================================================================
    # Step 4: 고급 기능 (advance - 상황 이미지)
    # =========================================================================
    print("\n[Step 4] 고급 기능 (advance) 주입...")
    time.sleep(1.0)
    if art.situation_image_path and art.situation_image_path.exists():
        file_inputs = page.locator("input[type='file']")
        if file_inputs.count() > 0:
            try:
                file_inputs.first.set_input_files(str(art.situation_image_path))
                print(f"   - 상황 이미지 업로드: {art.situation_image_path.name}")
                time.sleep(1.5)
            except Exception as e:
                print(f"   ⚠️ 상황 이미지 업로드 실패: {e}")

    # Step 4 완료 후 [다음] 클릭
    nxt_4 = page.locator("button:visible:has-text('다음')").first
    if nxt_4.count() > 0:
        try:
            nxt_4.click()
            time.sleep(2.0)
            print("   ✅ [다음] 버튼 클릭 -> Step 5(info) 이동")
        except Exception:
            switch_step_tab(page, "info", "캐릭터 상세")
    else:
        switch_step_tab(page, "info", "캐릭터 상세")

    # =========================================================================
    # Step 5: 캐릭터 상세 (info)
    # =========================================================================
    print("\n[Step 5] 캐릭터 상세 (info) 주입...")
    time.sleep(1.0)

    # Detail Description: textarea[placeholder*='캐릭터의 성격이나 서사']
    desc_ta = page.locator("textarea[placeholder*='캐릭터의 성격이나 서사']").first
    if desc_ta.count() > 0:
        fill_react_input(page, desc_ta, art.character_desc[:CHARACTER_DESC_MAX])
        print(f"   - 캐릭터 상세 설명: {crack_len(art.character_desc[:CHARACTER_DESC_MAX])}자")

    # Genre Selection (Radix Select combobox 0)
    print(f"   - 장르 선택 시도: {art.genre}...")
    try:
        combos = page.locator("button[role='combobox']:visible")
        if combos.count() >= 1:
            genre_btn = combos.nth(0)
            genre_btn.scroll_into_view_if_needed()
            genre_btn.click()
            time.sleep(0.8)

            # Available crack genres: SF/판타지, 일상/현대, 로맨스, 로판, 무협, 시대, GL, 시뮬레이션, 1:1 롤플레잉, 기타
            target_genre = art.genre
            if "판타지" in target_genre or "sf" in target_genre.lower():
                cand = "SF/판타지"
            elif "일상" in target_genre or "현대" in target_genre:
                cand = "일상/현대"
            elif "로판" in target_genre:
                cand = "로판"
            elif "로맨스" in target_genre:
                cand = "로맨스"
            elif "무협" in target_genre:
                cand = "무협"
            elif "시대" in target_genre:
                cand = "시대"
            elif "롤플레잉" in target_genre:
                cand = "1:1 롤플레잉"
            else:
                cand = target_genre

            opt = page.locator(f"[role='option']:visible:has-text('{cand}')").first
            if opt.count() == 0:
                for kw in ["SF/판타지", "판타지", "SF", "일상", "로맨스", "기타"]:
                    opt = page.locator(f"[role='option']:visible:has-text('{kw}')").first
                    if opt.count() > 0:
                        cand = kw
                        break

            if opt.count() > 0:
                opt.click()
                time.sleep(0.5)
                print(f"   ✅ 장르 선택 완료: {cand}")
            else:
                print(f"   ⚠️ 일치하는 장르 옵션을 찾지 못함 (요청: {art.genre})")
    except Exception as e:
        print(f"   ⚠️ 장르 선택 실패: {e}")

    # Target Selection (Radix Select combobox 1)
    print(f"   - 타겟 선택 시도: {art.target}...")
    try:
        combos = page.locator("button[role='combobox']:visible")
        if combos.count() >= 2:
            target_btn = combos.nth(1)
            target_btn.scroll_into_view_if_needed()
            target_btn.click()
            time.sleep(0.8)

            opt = page.locator(f"[role='option']:visible:has-text('{art.target}')").first
            if opt.count() == 0:
                opt = page.locator("[role='option']:visible:has-text('전체')").first

            if opt.count() > 0:
                opt.click()
                time.sleep(0.5)
                print(f"   ✅ 타겟 선택 완료: {art.target}")
            else:
                print(f"   ⚠️ 일치하는 타겟 옵션을 찾지 못함 (요청: {art.target})")
    except Exception as e:
        print(f"   ⚠️ 타겟 선택 실패: {e}")

    # Hashtags: input[placeholder*='단어 입력 후 엔터']
    if art.hashtags:
        tag_input = page.locator("input[placeholder*='단어 입력 후 엔터']").first
        if tag_input.count() > 0:
            print(f"   - 해시태그 입력 ({len(art.hashtags)}개)...")
            for t in art.hashtags[:HASHTAG_MAX]:
                clean_tag = t.lstrip("#").strip()[:10]
                if clean_tag:
                    fill_react_input(page, tag_input, clean_tag)
                    page.keyboard.press("Enter")
                    time.sleep(0.3)

    # =========================================================================
    # Draft Save / 임시저장
    # =========================================================================
    print("\n💾 [임시저장 진행]")
    draft_btn = page.locator("button:visible:has-text('임시저장')").first
    if draft_btn.count() > 0:
        try:
            draft_btn.click()
            time.sleep(3.0)
            print("   🎉 [임시저장] 완료!")
            print(f"   🔗 에디터 주소: {page.url}")
            return True
        except Exception as e:
            print(f"   ⚠️ 임시저장 클릭 실패: {e}")
            return False

    return True


def run_sync(
    char_dir: Path,
    target_url: str | None = None,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    headless: bool = False,
    auto_submit: bool = False,
) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright가 설치되지 않았습니다. tools/.venv-sync 를 이용해주세요.", file=sys.stderr)
        return 1

    art = load_character_artifacts(char_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"🚀 크랙(Crack) 캐릭터 에디터 자동 주입 도구: {art.name}")
    print(f"프로필 경로: {profile_dir}")
    print("=" * 70)

    with sync_playwright() as p:
        browser_args = ["--disable-blink-features=AutomationControlled"]
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            args=browser_args,
            viewport={"width": 1440, "height": 900},
        )

        page = context.pages[0] if context.pages else context.new_page()

        if target_url:
            print(f"🌐 지정된 캐릭터 에디터 URL로 이동: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        else:
            print(f"🌐 크랙 홈으로 이동: {DEFAULT_LOGIN_URL}")
            page.goto(DEFAULT_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2.0)
            navigate_to_create_character(page)

        time.sleep(1.5)
        inject_character_all(page, art)

        if not headless and not auto_submit:
            print("\n👀 브라우저가 열려 있습니다. 에디터 내용을 확인 후 터미널에서 Enter를 누르면 브라우저를 닫습니다.")
            try:
                input("Press Enter to finish...")
            except (EOFError, KeyboardInterrupt):
                print("\n비대화형 실행 환경입니다. 사용자가 화면을 확인할 수 있도록 60초간 브라우저를 유지합니다...")
                time.sleep(60)
        elif auto_submit:
            print("\n임시저장 완료 후 화면 확인을 위해 5초간 대기합니다...")
            time.sleep(5)

        context.close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Crack Character Chat Playwright Automation Sync Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # inspect
    p_insp = subparsers.add_parser("inspect", help="Inspect character chat artifacts and limits")
    p_insp.add_argument("char_dir", help="Path to character chat project (e.g. <story>/char_chat/<name>)")

    # sync
    p_sync = subparsers.add_parser("sync", help="Synchronize character chat to Crack editor")
    p_sync.add_argument("char_dir", help="Path to character chat project")
    p_sync.add_argument("--url", help="Direct URL to character editor (e.g. for existing character)")
    p_sync.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    p_sync.add_argument("--auto-submit", action="store_true", help="Auto draft save without interactive prompt")

    args = parser.parse_args()

    char_path = Path(args.char_dir).resolve()
    if args.command == "inspect":
        return run_inspect(char_path)
    elif args.command == "sync":
        return run_sync(char_path, target_url=args.url, headless=args.headless, auto_submit=args.auto_submit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
