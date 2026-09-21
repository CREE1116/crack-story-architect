#!/usr/bin/env bash
# 스토리챗 프로젝트 하나에 모든 규격 검사를 돌린다.
#   ./scripts/validate.sh examples/apocalypse
#   ./scripts/validate.sh my-project --allow-unbuilt   # 아직 컴파일 전인 프로젝트
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJ="${1:-$ROOT/examples/apocalypse}"
shift || true
C="$ROOT/scripts/checks"
FAIL=0

run() { echo; echo "── $1"; shift; "$@" || FAIL=1; }

run "원본 대비 신선도"  python3 "$C/check_freshness.py" "$PROJ"
run "프로젝트 구조"     python3 "$C/check_project_layout.py" "$PROJ" "$@"
run "이름 규칙"         python3 "$C/check_naming.py" "$PROJ"
run "쇼케이스 공개정보" python3 "$C/check_showcase.py" "$PROJ"

if [ -f "$PROJ/build/integrated-prompt-safe.md" ]; then
  run "기호 정의" python3 "$C/check_symbols.py" \
        "$PROJ/build/integrated-prompt-safe.md" "$PROJ/build/integrated-prompt-unsafe.md"
  run "키워드북 항목 한도" python3 "$C/check_keyword_book.py" "$PROJ"
fi

echo
[ "$FAIL" -eq 0 ] && echo "전체 통과" || echo "실패 있음"
exit "$FAIL"
