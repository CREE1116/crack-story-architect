#!/usr/bin/env python3
"""Check Crack character-chat artifacts and limits.

Validates that all character chat fields satisfy the platform specifications:
- Name: <= 30 chars
- Tagline: <= 30 chars
- Prompt: <= 2,000 chars
- Play Guide: <= 500 chars
- Character Description: <= 1,000 chars
- Intro: User <= 150 chars, Character <= 150 chars
- Example Dialogues: <= 10 pairs, each User <= 150 chars, Character <= 150 chars
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def crack_len(text: str) -> int:
    """UTF-16 surrogate-pair aware character count matching Crack platform."""
    if not text:
        return 0
    return max(len(text), len(text.encode("utf-16-le")) // 2)


def parse_dialogue_utterances(body: str) -> list[dict[str, str]]:
    """Extract ordered sequence of character and user utterances."""
    messages = []
    for line in body.splitlines():
        line = line.strip()
        m_char = re.match(r"^-\s*\*\*(?:캐릭터|인물|assistant)\*\*\s*:\s*(.+)$", line, re.I)
        m_user = re.match(r"^-\s*\*\*(?:유저|사용자|user)\*\*\s*:\s*(.+)$", line, re.I)
        if m_char:
            messages.append({"role": "character", "text": m_char.group(1).strip()})
        elif m_user:
            messages.append({"role": "user", "text": m_user.group(1).strip()})
    return messages


def parse_dialogues_md(content: str) -> tuple[str, list[dict[str, str]], list[list[dict[str, str]]]]:
    """Parse dialogues.md into situation background, intro sequence, and list of example sequences."""
    intro_bg = ""
    intro: list[dict[str, str]] = []
    examples: list[list[dict[str, str]]] = []

    sections = re.split(r"(?m)^##\s+", content)
    for sec in sections:
        if not sec.strip():
            continue
        lines = sec.strip().splitlines()
        header = lines[0].strip().lower()
        body = "\n".join(lines[1:])
        if ("상황 배경" in header or "시작 프롬프트" in header or "intro_bg" in header or "intro background" in header or ("배경" in header and "예시" not in header)) and "예시" not in header:
            intro_bg = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
        else:
            msgs = parse_dialogue_utterances(body)
            if not msgs:
                continue
            if "인트로" in header:
                intro = msgs
            elif "예시" in header or "대화" in header or "example" in header:
                examples.append(msgs)

    return intro_bg, intro, examples


def inspect_project(project_dir: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    lines: list[str] = []

    build_dir = project_dir / "build"
    has_build = build_dir.exists()

    # 1. Meta (Name, Tagline)
    name = ""
    tagline = ""
    genre = ""
    target = ""
    hashtags: list[str] = []

    meta_json = build_dir / "meta.json"
    meta_yaml = project_dir / "meta.yaml"

    if meta_json.exists():
        try:
            data = json.loads(meta_json.read_text(encoding="utf-8"))
            name = data.get("name", "")
            tagline = data.get("tagline", "")
            genre = data.get("genre", "")
            target = data.get("target", "")
            hashtags = data.get("hashtags", [])
        except Exception as e:
            errors.append(f"meta.json 파싱 실패: {e}")
    elif meta_yaml.exists():
        # Simple YAML parse fallback
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

    name_len = crack_len(name)
    tagline_len = crack_len(tagline)

    lines.append(f"{'항목':<18} | {'현재':<10} | {'제한':<10} | {'상태'}")
    lines.append("-" * 55)

    def check_stat(label: str, cur: int, max_val: int, req_min: int = 1) -> str:
        nonlocal errors
        if cur > max_val:
            errors.append(f"{label} 초과 ({cur} > {max_val})")
            return f"❌ 초과 ({cur}/{max_val})"
        elif cur < req_min:
            errors.append(f"{label} 누락 또는 빈 값")
            return "❌ 누락"
        return f"✅ PASS ({cur}/{max_val})"

    lines.append(f"{'캐릭터 이름':<18} | {name_len:<10} | {'<= 30자':<10} | {check_stat('캐릭터 이름', name_len, 30)}")
    lines.append(f"{'한줄소개':<18} | {tagline_len:<10} | {'<= 30자':<10} | {check_stat('한줄소개', tagline_len, 30)}")

    # 2. Prompt (<= 2000)
    prompt_text = ""
    prompt_path = build_dir / "prompt.md" if has_build else project_dir / "character.md"
    if prompt_path.exists():
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
    prompt_len = crack_len(prompt_text)
    lines.append(f"{'프롬프트':<18} | {prompt_len:<10} | {'<= 2000자':<10} | {check_stat('프롬프트', prompt_len, 2000)}")

    # 3. Play Guide (<= 500)
    guide_text = ""
    guide_path = build_dir / "play-guide.md"
    if guide_path.exists():
        guide_text = guide_path.read_text(encoding="utf-8").strip()
    elif (project_dir / "guide.md").exists():
        m = re.search(r"##\s*플레이가이드[^\n]*\n(.*?)(?=\n##|\Z)", (project_dir / "guide.md").read_text(encoding="utf-8"), re.S)
        if m:
            guide_text = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip()
    guide_len = crack_len(guide_text)
    lines.append(f"{'플레이가이드':<18} | {guide_len:<10} | {'<= 500자':<10} | {check_stat('플레이가이드', guide_len, 500)}")

    # 4. Character Description (<= 1000)
    desc_text = ""
    desc_path = build_dir / "character-desc.md"
    if desc_path.exists():
        desc_text = desc_path.read_text(encoding="utf-8").strip()
    elif (project_dir / "guide.md").exists():
        m = re.search(r"##\s*캐릭터 설명[^\n]*\n(.*?)(?=\n##|\Z)", (project_dir / "guide.md").read_text(encoding="utf-8"), re.S)
        if m:
            desc_text = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip()
    desc_len = crack_len(desc_text)
    lines.append(f"{'캐릭터 설명':<18} | {desc_len:<10} | {'<= 1000자':<10} | {check_stat('캐릭터 설명', desc_len, 1000)}")

    # 5. Situation Background (introBackground <= 500)
    intro_bg = ""
    intro_bg_path = build_dir / "intro-background.md"
    if intro_bg_path.exists():
        intro_bg = intro_bg_path.read_text(encoding="utf-8").strip()
    elif (project_dir / "dialogues.md").exists():
        intro_bg, _, _ = parse_dialogues_md((project_dir / "dialogues.md").read_text(encoding="utf-8"))

    intro_bg_len = crack_len(intro_bg)
    lines.append(f"{'상황 배경':<18} | {intro_bg_len:<10} | {'<= 500자':<10} | {check_stat('상황 배경', intro_bg_len, 500, req_min=0)}")

    # 6. Intro Dialogue (each utterance <= 150)
    intro_msgs: list[dict[str, str]] = []
    if (project_dir / "dialogues.md").exists():
        _, intro_msgs, _ = parse_dialogues_md((project_dir / "dialogues.md").read_text(encoding="utf-8"))
    elif (build_dir / "intro.json").exists():
        try:
            d = json.loads((build_dir / "intro.json").read_text(encoding="utf-8"))
            if isinstance(d, list):
                intro_msgs = d
            elif isinstance(d, dict):
                if d.get("user"):
                    intro_msgs.append({"role": "user", "text": d["user"]})
                if d.get("character"):
                    intro_msgs.append({"role": "character", "text": d["character"]})
        except Exception:
            pass

    intro_len_total = sum(crack_len(m.get("text", "")) for m in intro_msgs)
    intro_stat = "✅ PASS" if intro_msgs else "❌ 누락"
    for i, m in enumerate(intro_msgs, 1):
        mlen = crack_len(m.get("text", ""))
        if mlen > 150:
            errors.append(f"인트로 발화 {i} ({m.get('role')}) {mlen}자 초과")
            intro_stat = f"❌ 초과 ({mlen}/150)"
    lines.append(f"{'인트로 발화 수':<18} | {f'{len(intro_msgs)}개 ({intro_len_total}자)':<10} | {'각 <= 150자':<10} | {intro_stat}")

    # 7. Example Dialogues (Count <= 10, each <= 150)
    examples: list[Any] = []
    if (project_dir / "dialogues.md").exists():
        _, _, examples = parse_dialogues_md((project_dir / "dialogues.md").read_text(encoding="utf-8"))
    elif (build_dir / "examples.json").exists():
        try:
            examples = json.loads((build_dir / "examples.json").read_text(encoding="utf-8"))
        except Exception:
            pass

    ex_cnt = len(examples)
    ex_stat = "✅ PASS" if 0 <= ex_cnt <= 10 else f"❌ 초과 ({ex_cnt}/10)"
    if ex_cnt > 10:
        errors.append(f"예시 대화 개수 초과: {ex_cnt}개 (최대 10개)")
    lines.append(f"{'예시대화 세트 수':<18} | {ex_cnt:<10} | {'<= 10세트':<10} | {ex_stat}")

    for idx, ex_set in enumerate(examples, 1):
        if isinstance(ex_set, list):
            for mi, m in enumerate(ex_set, 1):
                mlen = crack_len(m.get("text", ""))
                if mlen > 150:
                    errors.append(f"예시대화 {idx} 발화 {mi} {mlen}자 초과")
        elif isinstance(ex_set, dict):
            eu = crack_len(ex_set.get("user", ""))
            ec = crack_len(ex_set.get("character", ""))
            if eu > 150:
                errors.append(f"예시대화 {idx} 유저 발화 {eu}자 초과")
            if ec > 150:
                errors.append(f"예시대화 {idx} 캐릭터 발화 {ec}자 초과")

    # 7. Images
    thumb = project_dir / "assets" / "thumbnail.webp"
    thumb_png = project_dir / "assets" / "thumbnail.png"
    has_thumb = thumb.exists() or thumb_png.exists()
    lines.append(f"{'대표 썸네일':<18} | {'존재' if has_thumb else '없음':<10} | {'권장':<10} | {'✅ 준비됨' if has_thumb else '⚠️ 미등록'}")

    sit_img = project_dir / "assets" / "situation.webp"
    sit_png = project_dir / "assets" / "situation.png"
    has_sit = sit_img.exists() or sit_png.exists()
    lines.append(f"{'상황/배경 이미지':<18} | {'존재' if has_sit else '없음':<10} | {'선택':<10} | {'✅ 준비됨' if has_sit else 'ℹ️ 선택사항'}")

    return len(errors) == 0, lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Crack character-chat limits.")
    parser.add_argument("project", help="Path to character-chat project directory")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        print(f"Error: Directory {project_dir} does not exist", file=sys.stderr)
        return 1

    ok, report_lines = inspect_project(project_dir)
    print("\n" + "\n".join(report_lines) + "\n")

    if ok:
        print("🎉 모든 캐릭터챗 규격을 만족합니다 (PASS).")
        return 0
    else:
        print("❌ 일부 항목이 크랙 규격 한도를 초과하거나 누락되었습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
