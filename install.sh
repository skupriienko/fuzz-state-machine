#!/usr/bin/env bash
# ==============================================================================
# Fuzz State Machine Engine — Universal Installer & AI Tool Integrator
# ==============================================================================
# Installs fsm-engine and immediately injects the Mandatory Planning Invariant
# into all major AI tools:
# - Claude Code (CLAUDE.md)
# - Gemini CLI & Antigravity (GEMINI.md, AGENTS.md)
# - Cursor (.cursorrules, .cursor/rules/fsm-planning.mdc)
# - Windsurf (.windsurfrules)
# - Kilo / KiloCode (.kilo/kilo.jsonc, .kilo/rules/fsm-planning.md, .kilocoderules)
# - GitHub Copilot (.github/copilot-instructions.md)
# - Aider / OpenCode (CONVENTIONS.md)
#
# Zero dependencies: Pure POSIX shell & Python Standard Library.
# ==============================================================================

set -euo pipefail

# ANSI Colors
BOLD="\033[1m"
GREEN="\033[32m"
BLUE="\033[34m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

log_info() { echo -e "${CYAN}ℹ [INFO]${RESET} $*"; }
log_ok()   { echo -e "${GREEN}✔ [OK]${RESET} $*"; }
log_warn() { echo -e "${YELLOW}⚠ [WARN]${RESET} $*"; }
log_err()  { echo -e "${RED}✖ [ERR]${RESET} $*" >&2; }

echo -e "${BOLD}${BLUE}"
echo "================================================================================"
echo "      FUZZ STATE MACHINE ENGINE — MANDATORY PLANNING INVARIANT INSTALLER        "
echo "================================================================================"
echo -e "${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-${PWD}}"

log_info "Target project directory: ${TARGET_DIR}"

# 1. Install CLI binary
mkdir -p "${TARGET_DIR}/bin"
cp "${SCRIPT_DIR}/bin/fsm-engine" "${TARGET_DIR}/bin/fsm-engine"
chmod +x "${TARGET_DIR}/bin/fsm-engine"
log_ok "CLI installed -> ${TARGET_DIR}/bin/fsm-engine"

# 2. Install Agent Skill & Module integration
SKILLS_DIR="${TARGET_DIR}/.agents/skills/fuzz-state-machine"
mkdir -p "${SKILLS_DIR}/src"
cp "${SCRIPT_DIR}/SKILL.md" "${SKILLS_DIR}/SKILL.md"
cp -r "${SCRIPT_DIR}/src/fuzz_state_machine" "${SKILLS_DIR}/src/"
log_ok "Agent Skill & library installed -> ${SKILLS_DIR}"

# 3. Inject Mandatory Planning Invariant into ALL AI Tools
INSTRUCTION_SNIPPET=$(cat <<'EOF'

<!-- MANDATORY PLANNING INVARIANT: FUZZ STATE MACHINE -->
### 🔒 Mandatory Plan State-Machine & Fuzz Invariant
Before presenting or executing any non-trivial multi-step plan or architecture:
1. Every plan MUST declare a formal state machine block (states, start, terminals, transitions):
   ```yaml
   states: [draft, review, approved]
   start: draft
   terminals: [approved]
   transitions:
     - { from: draft, to: review }
     - { from: review, to: approved }
   ```
2. Validate with: `fsm-engine validate <path_to_plan.md>`
3. Enforcement: Only plans passing `PLAN_FUZZ:100/100 EXIT:0` (0 deadlocks, 0 ghost states, terminal reachability verified) are permitted for execution.
<!-- END MANDATORY PLANNING INVARIANT -->
EOF
)

append_rule() {
    local file="$1"
    local tool_name="$2"
    mkdir -p "$(dirname "${file}")"
    if [[ ! -f "${file}" ]]; then
        echo "# Project AI Instructions" > "${file}"
    fi
    if ! grep -q "MANDATORY PLANNING INVARIANT" "${file}"; then
        echo "${INSTRUCTION_SNIPPET}" >> "${file}"
        log_ok "[${tool_name}] Injected planning invariant -> ${file}"
    else
        log_ok "[${tool_name}] Planning invariant already present -> ${file}"
    fi
}

append_rule "${TARGET_DIR}/CLAUDE.md" "Claude Code"
append_rule "${TARGET_DIR}/GEMINI.md" "Gemini CLI / Antigravity"
append_rule "${TARGET_DIR}/AGENTS.md" "Universal Agents"
append_rule "${TARGET_DIR}/.cursorrules" "Cursor Legacy"
append_rule "${TARGET_DIR}/.windsurfrules" "Windsurf Cascade"
append_rule "${TARGET_DIR}/.github/copilot-instructions.md" "GitHub Copilot"
append_rule "${TARGET_DIR}/CONVENTIONS.md" "Aider / OpenCode"

# Cursor MDC modern rule
CURSOR_MDC="${TARGET_DIR}/.cursor/rules/fsm-planning.mdc"
mkdir -p "$(dirname "${CURSOR_MDC}")"
cat <<'EOF' > "${CURSOR_MDC}"
---
description: Mandatory Plan State Machine Invariant and Path Fuzzing Gate
globs: "**/*plan*.md,**/*tasks*.md"
alwaysApply: true
---
When authoring or executing any multi-step plan, declare the state machine (states, start, terminals, transitions)
and execute `fsm-engine validate <plan.md>`. Proceed only when `PLAN_FUZZ:100/100 EXIT:0` passes.
EOF
log_ok "[Cursor MDC] Rule created -> ${CURSOR_MDC}"

# Kilo / KiloCode integration (.kilo/kilo.jsonc and .kilo/rules/fsm-planning.md)
KILO_DIR="${TARGET_DIR}/.kilo"
mkdir -p "${KILO_DIR}/rules"
KILO_CONFIG="${KILO_DIR}/kilo.jsonc"
if [[ ! -f "${KILO_CONFIG}" ]]; then
    cat <<'EOF' > "${KILO_CONFIG}"
{
  "$schema": "https://app.kilo.ai/config.json",
  "instructions": [
    ".kilo/rules/*.md"
  ]
}
EOF
fi

cat <<'EOF' > "${KILO_DIR}/rules/fsm-planning.md"
# Mandatory Plan State-Machine & Fuzz Invariant

Before presenting or executing any non-trivial multi-step plan:
1. Declare a formal state machine block (states, start, terminals, transitions):
   ```yaml
   states: [draft, review, approved]
   start: draft
   terminals: [approved]
   transitions:
     - { from: draft, to: review }
     - { from: review, to: approved }
   ```
2. Validate with: `fsm-engine validate <plan.md>`
3. Enforcement: Only plans passing `PLAN_FUZZ:100/100 EXIT:0` (0 deadlocks, 0 ghost states, terminal reachability verified) are permitted for execution.
EOF
log_ok "[Kilo / KiloCode] Rule created -> ${KILO_DIR}/rules/fsm-planning.md"

# KiloCode legacy compatibility (.kilocoderules)
append_rule "${TARGET_DIR}/.kilocoderules" "KiloCode Legacy"

# 4. Output receipt
cat <<RECEIPT

================================================================================
                    INSTALLATION COMPLETED SUCCESSFULLY                         
================================================================================

[RECEIPT]
- Status: INSTALLED & INTEGRATED
- Target Directory: ${TARGET_DIR}
- CLI Executable: ${TARGET_DIR}/bin/fsm-engine
- Agent Skill: ${SKILLS_DIR}/SKILL.md
- Configured AI Endpoints:
    • Claude Code      : ${TARGET_DIR}/CLAUDE.md
    • Gemini / AGY     : ${TARGET_DIR}/GEMINI.md & AGENTS.md
    • Cursor           : ${TARGET_DIR}/.cursorrules & ${CURSOR_MDC}
    • Windsurf         : ${TARGET_DIR}/.windsurfrules
    • Kilo / KiloCode  : ${KILO_DIR}/kilo.jsonc & ${KILO_DIR}/rules/fsm-planning.md
    • GitHub Copilot   : ${TARGET_DIR}/.github/copilot-instructions.md
    • Aider / OpenCode : ${TARGET_DIR}/CONVENTIONS.md

Every AI tool will now automatically enforce formal state machine path fuzzing for any planning task!
RECEIPT
