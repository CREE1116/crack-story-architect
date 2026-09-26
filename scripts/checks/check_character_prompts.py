#!/usr/bin/env python3
"""build/assets/characters*.json 의 인물 베이스 프롬프트가 외형 지침을 따르는지 본다.

characters.json 외에 characters-stars.json 같은 보조 캐스트 파일도 같은 규칙으로 본다.

references/character-visual-design.md §8~9 의 기계로 잡을 수 있는 부분만 검사한다.
색 조화·실루엣 겹침처럼 눈으로 봐야 하는 것은 잡지 못한다.

FAIL
  - 키가 name/prompt/uc 가 아님
  - 가중치 ``::`` 짝이 안 맞음
  - 프롬프트 600자 초과 (그림체가 깨진다)
  - 자연어 문장이 ``.,`` 로 닫히지 않거나 문장 안에 쉼표가 있음
  - 표정·배경·나이 숫자·cm 가 프롬프트에 있음
  - 같은 태그가 prompt 와 uc 에 동시에 있음
  - 두 인물의 헤어 가중치 묶음이 똑같음
WARN
  - 450자 초과, 가중치 묶음 3개 이상, 자연어 문장 3개 이상
  - uc 에 표정 태그 (감정 프리셋의 해당 컷이 막힌다)
  - 같은 태그가 prompt 안에 두 번

파일이 없으면 SKIP.

사용:
    check_character_prompts.py PROJECT_DIR
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HARD_MAX, SOFT_MAX = 600, 450
EXPRESSION = {
    "smile", "smiling", "grin", "laughing", "frown", "crying", "tears", "angry",
    "calm", "expressionless", "confident", "gentle", "serious", "blush", "pout", "smirk",
}
BACKGROUND = {"outdoors", "indoors", "background", "simple background", "white background", "scenery"}
NUMERIC = re.compile(r"\b\d+\s*(?:yo|cm)\b", re.I)
WEIGHT = re.compile(r"\d(?:\.\d+)?::(.*?)::")
SENTENCE = re.compile(r"(?:(?<=^)|(?<=, )|(?<=::, ))([A-Z][^,]*)(,|$)")


def tags(text: str) -> list[str]:
    plain = re.sub(r"\d(?:\.\d+)?::|::", "", text)
    return [t.strip().lower() for t in plain.split(",") if t.strip() and not t.strip()[0].isupper()]


def check_one(c: dict) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    name = c.get("name", "?")
    if set(c) != {"name", "prompt", "uc"}:
        fails.append(f"{name}: 키는 name/prompt/uc 셋뿐이어야 합니다 (현재 {sorted(c)})")
        return fails, warns
    p, uc = c["prompt"], c["uc"]
    if p.count("::") % 2:
        fails.append(f"{name}: 가중치 :: 짝이 맞지 않습니다")
    n = len(p.encode("utf-16-le")) // 2
    if n > HARD_MAX:
        fails.append(f"{name}: 프롬프트 {n}자 > {HARD_MAX} (그림체가 깨집니다)")
    elif n > SOFT_MAX:
        warns.append(f"{name}: 프롬프트 {n}자 > {SOFT_MAX}")
    groups = WEIGHT.findall(p)
    if len(groups) > 2:
        warns.append(f"{name}: 가중치 묶음 {len(groups)}개 (헤어·눈 2곳 권장)")
    sentences = SENTENCE.findall(p)
    for s, _ in sentences:
        if not s.endswith("."):
            fails.append(f"{name}: 자연어가 마침표 전에 끊겼습니다(문장 안 쉼표?) → {s[:40]}")
    for m in re.finditer(r"\.(?!,)(?=\s*$)", p):
        fails.append(f"{name}: 마지막 문장을 '.,' 로 닫지 않았습니다")
    if len(sentences) > 2:
        warns.append(f"{name}: 자연어 문장 {len(sentences)}개 (1~2개 권장)")
    tp, tu = tags(p), tags(uc)
    bad = sorted((set(tp) & EXPRESSION) | (set(tp) & BACKGROUND))
    if bad:
        fails.append(f"{name}: 표정·배경 태그는 베이스에 넣지 않습니다 → {', '.join(bad)}")
    if NUMERIC.search(p):
        fails.append(f"{name}: 나이·키 숫자는 정본에만 적습니다 → {NUMERIC.search(p).group(0)}")
    dup = sorted({x for x in tp if tp.count(x) > 1})
    if dup:
        warns.append(f"{name}: 같은 태그가 두 번 → {', '.join(dup)}")
    both = sorted(set(tp) & set(tu))
    if both:
        fails.append(f"{name}: prompt 와 uc 에 같은 태그 → {', '.join(both)}")
    uc_expr = sorted(set(tu) & EXPRESSION)
    if uc_expr:
        warns.append(f"{name}: uc 의 표정 태그가 감정 컷을 막습니다 → {', '.join(uc_expr)}")
    return fails, warns


def validate(project: Path) -> bool:
    paths = sorted((project / "build/assets").glob("characters*.json"))
    if not paths:
        print(f"SKIP {project}: build/assets/characters*.json 없음")
        return True
    ok = True
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        fails: list[str] = []
        warns: list[str] = []
        hair: dict[str, str] = {}
        for c in data:
            f, w = check_one(c)
            fails += f
            warns += w
            groups = WEIGHT.findall(c.get("prompt", ""))
            if groups:
                key = ",".join(sorted(t.strip() for t in groups[0].split(",")))
                if key in hair:
                    fails.append(f"{c.get('name')}: 헤어 묶음이 {hair[key]}와 똑같습니다")
                hair.setdefault(key, c.get("name", "?"))
        rel = path.relative_to(project)
        for w in warns:
            print(f"WARN {rel} {w}")
        for f in fails:
            print(f"FAIL {rel} {f}")
        if not fails:
            print(f"PASS {rel}: {len(data)}명")
        ok = ok and not fails
    return ok


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    return 0 if validate(Path(argv[1])) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
