#!/usr/bin/env python3
"""Derive a Crack Character Chat from an existing Story Chat project.

Extracts a character's persona, speech register, relationship with the player,
and world context from `story.md` and `characters.md` into a dedicated
1:1 character-chat project structure satisfying all platform limits:
- Prompt <= 2,000 chars
- Play Guide <= 500 chars
- Character Description <= 1,000 chars
- Intro Dialogue (User <= 150, Character <= 150)
- Example Dialogues (<= 10 pairs, each <= 150)
- Meta: Name <= 30, Tagline <= 30

Usage:
    python3 scripts/derive_character_chat.py examples/apocalypse "서린"
    python3 scripts/derive_character_chat.py examples/apocalypse "서린" --output characters/seorin
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def crack_len(text: str) -> int:
    return max(len(text), len(text.encode("utf-16-le")) // 2)


def extract_character_block(characters_text: str, target_name: str) -> tuple[str, str, str]:
    """Finds the character section matching target_name.
    Returns (raw_name, title_badge, full_section_text).
    """
    pattern = r"(?m)^##\s+([^\n「]+)(?:「([^」]+)」)?\s*$"
    matches = list(re.finditer(pattern, characters_text))
    
    target_clean = target_name.strip()
    for i, m in enumerate(matches):
        c_name = m.group(1).strip()
        badge = m.group(2).strip() if m.group(2) else ""
        if target_clean in c_name or c_name in target_clean:
            start_pos = m.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(characters_text)
            return c_name, badge, characters_text[start_pos:end_pos].strip()

    raise ValueError(f"캐릭터 '{target_name}'을(를) characters.md 에서 찾을 수 없습니다.")


def extract_field(section_text: str, field_name: str) -> str:
    pattern = rf"(?i)-\s*{re.escape(field_name)}\s*:\s*([^\n]+)"
    m = re.search(pattern, section_text)
    return m.group(1).strip() if m else ""


def derive_character(story_dir: Path, character_name: str, out_dir: Path) -> Path:
    story_md_path = story_dir / "story.md"
    chars_md_path = story_dir / "characters.md"

    if not story_md_path.exists() or not chars_md_path.exists():
        raise FileNotFoundError(f"{story_dir}에 story.md 또는 characters.md 가 없습니다.")

    story_text = story_md_path.read_text(encoding="utf-8")
    chars_text = chars_md_path.read_text(encoding="utf-8")

    name, badge, block = extract_character_block(chars_text, character_name)
    print(f"📖 캐릭터 발견: {name} (직함: {badge or '없음'})")

    # Story Core 추출
    premise = extract_field(story_text, "Premise")
    tone_genre = extract_field(story_text, "Tone / genre / intended ending shape")
    genre_m = re.search(r"-\s*genre\s*:\s*([^\n]+)", story_text, re.IGNORECASE)
    genre = genre_m.group(1).strip() if genre_m else "판타지/SF"

    # Character 상세 추출
    role = extract_field(block, "Role / current goal")
    contradiction = extract_field(block, "Core desire / self-image / contradiction")
    boundary = extract_field(block, "Orientation and relationship boundary")
    speech_reg = extract_field(block, "Speech register / vocabulary / avoided habit")
    appearance = extract_field(block, "실루엣·체격·키 인상")
    hair = extract_field(block, "머리 (색·길이·정리 방식)")
    eyes = extract_field(block, "눈 (색·인상)")
    outfit = extract_field(block, "복장·소속 표식")
    point = extract_field(block, "식별 포인트")

    # Sample lines
    sample_lines: dict[str, str] = {}
    for line in block.splitlines():
        sm = re.match(r"\s*-\s*([a-zA-Z_\s]+)\s*:\s*\"([^\"]+)\"", line)
        if sm:
            sample_lines[sm.group(1).strip().lower()] = sm.group(2).strip()

    # Relationship with player
    rel_match = re.search(r"\|\s*플레이어\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|", block)
    rel_stage = rel_match.group(1).strip() if rel_match else "초면/경계"
    rel_tension = rel_match.group(2).strip() if rel_match else ""
    rel_stance = rel_match.group(4).strip() if rel_match else ""

    # 1. Name & Tagline (<= 30자)
    clean_name = name[:30]
    tagline = f"{badge} {name}".strip()
    if len(tagline) > 30:
        tagline = f"{name}과의 1:1 대화"[:30]

    # 2. Compile System Prompt (<= 2,000 chars)
    prompt_sections = [
        f"# {clean_name} — 1:1 캐릭터챗 시스템 프롬프트",
        "",
        "## 핵심 정체성 & 성격",
        f"- 신분/역할: {badge} ({role})",
        f"- 핵심 심리: {contradiction}",
        f"- 성격 및 태도: 평소에는 차분하고 절제되어 있으나 내면에 인간적인 고뇌와 결핍을 지님.",
        "",
        "## 대화 스타일 & 말투",
        f"- 어조/어휘: {speech_reg or '캐릭터 특유의 말투를 일관되게 유지'}",
        "- 1:1 채팅 감각: 3인칭 소설식 지문(지나치게 긴 배경 묘사)을 최소화하고, 유저와 직접 주고받는 대화와 실시간 반응에 집중한다.",
    ]
    if sample_lines:
        prompt_sections.append("- 대표 대사 예시:")
        for k, v in list(sample_lines.items())[:4]:
            prompt_sections.append(f"  * {k}: \"{v}\"")

    prompt_sections.extend([
        "",
        "## 플레이어와의 관계 & 대화 규칙",
        f"- 현재 관계: {rel_stage} ({rel_stance})",
        f"- 관계 발전: 유저의 태도와 신뢰도에 따라 점진적으로 경계를 풀고 솔직한 속내를 드러냄.",
        f"- 바운더리: {boundary or '캐릭터의 신념과 일관성을 지키며 대화'}",
        "- 절대 원칙: 캐릭터의 원래 성격과 말투를 깨뜨리는 부자연스러운 순응이나 메타 발언을 하지 않는다.",
    ])
    prompt_text = "\n".join(prompt_sections).strip()

    # 3. Play Guide (<= 500 chars)
    guide_lines = [
        f"당신은 {clean_name}과(와) 1:1로 직접 마주하고 대화하고 있습니다.",
        f"{clean_name}은(는) 현재 {rel_stage} 상태입니다.",
        "💡 대화 팁:",
        f"- {role or '현재 상황'}에 대해 물어보거나 공감을 표해보세요.",
        "- 무리하게 다가가기보다는 진지하게 신뢰를 쌓아가면 조금씩 마음을 엽니다.",
    ]
    play_guide_text = "\n".join(guide_lines).strip()

    # 4. Character Description (<= 1,000 chars)
    desc_lines = [
        f"「{tagline}」",
        "",
        f"{clean_name} {f'({badge})' if badge else ''}",
        f"• 외모: {appearance or ''} {hair or ''} {eyes or ''}".strip(),
        f"• 특징: {point or '매력적인 분위기'}",
        f"• 성향: {contradiction or '신뢰할 수 있는 파트너'}",
        "",
        f"{role or '위험한 세계 속에서 마주친 인물'}.",
        f"지금 {clean_name}과(와) 단둘만의 대화를 시작해보세요.",
    ]
    char_desc_text = "\n".join(desc_lines).strip()

    # 5. Situation Background (<= 500 chars)
    bg_parts = []
    if premise:
        bg_parts.append(premise.rstrip("."))
    if role:
        bg_parts.append(f"{clean_name}은(는) {role}")
    if rel_tension:
        bg_parts.append(f"플레이어와의 관계: {rel_stage} ({rel_tension})")
    bg_parts.append(f"유저와 마주친 현장에서 {clean_name}의 고유한 세계관과 심리 상태를 유지하며 1:1 대화를 진행한다.")
    intro_bg_text = ". ".join(bg_parts)
    if len(intro_bg_text) > 490:
        intro_bg_text = intro_bg_text[:485] + "…"

    # 6. Intro & Examples (<= 150 chars each)
    intro_user = f"{clean_name}, 잠깐 얘기 좀 할 수 있어?"
    intro_char = sample_lines.get("guarded") or sample_lines.get("relaxed") or f"…무슨 일이지? 할 말이 있다면 짧게 해."
    if len(intro_char) > 150:
        intro_char = intro_char[:145] + "…"

    examples = [
        {
            "user": "괜찮아 보여서 다행이네. 무리하고 있는 건 아니지?",
            "character": sample_lines.get("relaxed") or "…신경 쓸 필요 없어. 내 상태는 내가 가장 잘 아니까.",
        },
        {
            "user": "방금 한 말 진심이야? 왜 그렇게까지 스스로를 몰아세워?",
            "character": sample_lines.get("angry or hurt") or "…더 이상 묻지 마. 이건 내가 짊어져야 할 몫이야.",
        },
        {
            "user": "오늘 네 판단 덕분에 살았어. 고마워.",
            "character": sample_lines.get("trusting") or "네가 잘 따라와 준 덕분이야. …다음에도 부탁하지.",
        }
    ]

    # Output directory setup
    out_dir.mkdir(parents=True, exist_ok=True)
    build_dir = out_dir / "build"
    assets_dir = out_dir / "assets"
    build_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Write source files
    (out_dir / "character.md").write_text(block, encoding="utf-8")
    
    dialogues_md = f"""# Dialogues (Intro & Examples)

<!-- 캐릭터 1명과 1:1로 직접 채팅(대화)하는 실시간 메신저/대면 감각의 대화 세트입니다.
     - 상황 배경: 유저에게는 보이지 않지만 캐릭터가 인지하고 있어야 하는 시작 프롬프트(최대 500자)
     - 인트로: 첫 조우 시의 실제 대화 말풍선 시퀀스 (각 발화 최대 150자)
     - 예시 대화: 캐릭터의 말투·태도·입체적 매력을 보여주는 티키타카 시퀀스 (최대 10세트, 각 발화 최대 150자) -->

## 상황 배경 (시작 프롬프트)
<!-- 사용자에게는 보이지 않지만 캐릭터는 알고 있어야 하는 상황 배경을 작성합니다 (최대 500자).
     스토리챗의 시작 프롬프트와 같은 역할을 합니다. -->
{intro_bg_text}

---

## 인트로
- **캐릭터**: {intro_char}
- **유저**: {intro_user}
- **캐릭터**: …무슨 말을 하려는지 들어보지. 계속해.

---

"""
    for idx, ex in enumerate(examples, 1):
        dialogues_md += f"""## 예시 대화 {idx}
- **유저**: {ex['user']}
- **캐릭터**: {ex['character']}

"""
    (out_dir / "dialogues.md").write_text(dialogues_md.strip(), encoding="utf-8")

    guide_md = f"""# Guide & Description

## 플레이가이드
{play_guide_text}

---

## 캐릭터 설명
{char_desc_text}
"""
    (out_dir / "guide.md").write_text(guide_md.strip(), encoding="utf-8")

    meta_dict = {
        "name": clean_name,
        "tagline": tagline,
        "genre": genre if len(genre) < 10 else "판타지",
        "target": "전체",
        "hashtags": [f"#{clean_name}", "#캐릭터챗", "#티키타카"],
    }
    (out_dir / "meta.yaml").write_text(
        f"""name: "{meta_dict['name']}"
tagline: "{meta_dict['tagline']}"
genre: "{meta_dict['genre']}"
target: "{meta_dict['target']}"
hashtags:
  - "#{clean_name}"
  - "#캐릭터챗"
  - "#티키타카"
""",
        encoding="utf-8"
    )

    # Write build artifacts
    (build_dir / "prompt.md").write_text(prompt_text, encoding="utf-8")
    (build_dir / "play-guide.md").write_text(play_guide_text, encoding="utf-8")
    (build_dir / "character-desc.md").write_text(char_desc_text, encoding="utf-8")
    (build_dir / "intro.json").write_text(json.dumps({"user": intro_user, "character": intro_char}, ensure_ascii=False, indent=2), encoding="utf-8")
    (build_dir / "examples.json").write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")
    (build_dir / "meta.json").write_text(json.dumps(meta_dict, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✨ 캐릭터챗 프로젝트 생성 완료: {out_dir}")
    print(f"   - 프롬프트: {crack_len(prompt_text)}자 (한도 2000자)")
    print(f"   - 플레이가이드: {crack_len(play_guide_text)}자 (한도 500자)")
    print(f"   - 캐릭터설명: {crack_len(char_desc_text)}자 (한도 1000자)")
    print(f"   - 인트로: 유저 {crack_len(intro_user)}자 / 캐릭터 {crack_len(intro_char)}자 (각 한도 150자)")
    print(f"   - 예시대화: {len(examples)}세트 (한도 10세트)")

    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Derive character chat from story project.")
    parser.add_argument("story_dir", help="Path to story project directory (containing story.md and characters.md)")
    parser.add_argument("character_name", help="Name of character to extract")
    parser.add_argument("--output", "-o", help="Target character directory (default: <story_dir>/characters/<slug>)")
    args = parser.parse_args()

    story_path = Path(args.story_dir).resolve()
    target_name = args.character_name.strip()
    
    if args.output:
        out_path = Path(args.output).resolve()
    else:
        # Default subfolder in story directory: char_chat/<character_name>
        slug = re.sub(r"[^\w\-가-힣]", "", target_name) or "char"
        out_path = story_path / "char_chat" / slug

    try:
        derive_character(story_path, target_name, out_path)
        return 0
    except Exception as e:
        print(f"❌ 실패: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
