#!/usr/bin/env bash
# ==============================================================================
# Crack Story Architect - Multi-Agent Skill Installer & Registrar
# ==============================================================================
# Usage:
#   ./scripts/install.sh <agent> [workspace_path]
#
# Supported agents:
#   antigravity   Google Antigravity (.agents/skills)
#   claude        Anthropic Claude Code (.claude/skills or global)
#   cursor        Cursor IDE (.cursor/rules/crack-story-architect.mdc)
#   windsurf      Windsurf IDE (.windsurfrules)
#   roo           Roo Code / Cline (.clinerules/crack-story-architect.md)
#   aider         Aider (.aider.conf.yml)
#   all           Install/register to all supported agents
# ==============================================================================

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_NAME="crack-story-architect"

TARGET="${1:-help}"
WORKSPACE="${2:-$(pwd)}"

print_usage() {
    echo "Usage: $0 <agent> [workspace_path]"
    echo ""
    echo "Available agents:"
    echo "  antigravity  Install into .agents/skills for Antigravity"
    echo "  claude       Install into .claude/skills for Claude Code"
    echo "  cursor       Generate .cursor/rules MDC rule for Cursor"
    echo "  windsurf     Register rule in .windsurfrules for Windsurf"
    echo "  roo          Register rule in .clinerules for Roo Code / Cline"
    echo "  aider        Configure Aider .aider.conf.yml"
    echo "  all          Register into all agents in the target workspace"
    echo ""
    echo "Example:"
    echo "  $0 antigravity /path/to/my-project"
    echo "  $0 claude --global"
    echo "  $0 all /path/to/my-project"
}

install_antigravity() {
    local target_dir="$WORKSPACE/.agents/skills/$SKILL_NAME"
    echo "🔗 Installing to Google Antigravity: $target_dir"
    mkdir -p "$WORKSPACE/.agents/skills"
    rm -rf "$target_dir"
    ln -s "$SKILL_DIR" "$target_dir"
    echo "✅ Antigravity skill registered successfully!"
}

install_claude() {
    if [ "${2:-}" = "--global" ] || [ "$WORKSPACE" = "--global" ]; then
        local target_dir="$HOME/.claude/skills/$SKILL_NAME"
        echo "🔗 Installing globally for Claude Code: $target_dir"
        mkdir -p "$HOME/.claude/skills"
        rm -rf "$target_dir"
        ln -s "$SKILL_DIR" "$target_dir"
        echo "✅ Claude Code global skill registered successfully!"
    else
        local target_dir="$WORKSPACE/.claude/skills/$SKILL_NAME"
        echo "🔗 Installing locally for Claude Code: $target_dir"
        mkdir -p "$WORKSPACE/.claude/skills"
        rm -rf "$target_dir"
        ln -s "$SKILL_DIR" "$target_dir"
        echo "✅ Claude Code project skill registered successfully!"
    fi
}

install_cursor() {
    local rule_dir="$WORKSPACE/.cursor/rules"
    local rule_file="$rule_dir/$SKILL_NAME.mdc"
    echo "📝 Generating Cursor MDC Rule: $rule_file"
    mkdir -p "$rule_dir"
    cat << RULE_EOF > "$rule_file"
---
description: Crack Story Chat Architect (Prompt & Asset Engine)
globs: ["story.md", "characters.md", "build/**", "start-sets/**", "deploy/**"]
alwaysApply: false
---

# Crack Story Architect Guidelines
When designing, compiling, or auditing Crack interactive story chats in this workspace:
1. Always follow the 3-Stage Pipeline (Authoring -> Compiling -> Derived Assets).
2. Adhere to platform limits: Prompts <= 7,000 chars, Openings <= 1,000 chars, Keyword books <= 400 chars.
3. Use the master reference guide: "$SKILL_DIR/SKILL.md".
4. Refer to the reference manual: "$SKILL_DIR/references/".
RULE_EOF
    echo "✅ Cursor MDC rule registered successfully!"
}

install_windsurf() {
    local rule_file="$WORKSPACE/.windsurfrules"
    echo "📝 Registering Windsurf Rule: $rule_file"
    touch "$rule_file"
    if ! grep -q "crack-story-architect" "$rule_file" 2>/dev/null; then
        cat << RULE_EOF >> "$rule_file"

# Crack Story Architect Integration
# Skill Path: $SKILL_DIR
When authoring or compiling Crack story chats (story.md, characters.md, build/*), follow the master guidelines at $SKILL_DIR/SKILL.md.
RULE_EOF
    fi
    echo "✅ Windsurf rule registered successfully!"
}

install_roo() {
    local rule_dir="$WORKSPACE/.clinerules"
    local rule_file="$rule_dir/$SKILL_NAME.md"
    echo "📝 Registering Roo Code / Cline Rule: $rule_file"
    mkdir -p "$rule_dir"
    cat << RULE_EOF > "$rule_file"
# Crack Story Architect Mode
Follow the comprehensive specifications at:
$SKILL_DIR/SKILL.md
and reference documentation at:
$SKILL_DIR/references/
RULE_EOF
    echo "✅ Roo Code / Cline rule registered successfully!"
}

install_aider() {
    local conf_file="$WORKSPACE/.aider.conf.yml"
    echo "📝 Configuring Aider: $conf_file"
    touch "$conf_file"
    if ! grep -q "crack-story-architect" "$conf_file" 2>/dev/null; then
        cat << RULE_EOF >> "$conf_file"
# Crack Story Architect Skill
read:
  - $SKILL_DIR/SKILL.md
RULE_EOF
    fi
    echo "✅ Aider configuration updated successfully!"
}

case "$TARGET" in
    antigravity)
        install_antigravity
        ;;
    claude)
        install_claude "$@"
        ;;
    cursor)
        install_cursor
        ;;
    windsurf)
        install_windsurf
        ;;
    roo|cline)
        install_roo
        ;;
    aider)
        install_aider
        ;;
    all)
        echo "🚀 Registering Crack Story Architect to ALL agents in $WORKSPACE..."
        install_antigravity
        install_claude "$@"
        install_cursor
        install_windsurf
        install_roo
        install_aider
        echo "🎉 All agent registrations complete!"
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
