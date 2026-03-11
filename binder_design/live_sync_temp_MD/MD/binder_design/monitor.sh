#!/bin/bash
# ================================================================
# monitor.sh — Live Pipeline Progress Dashboard
# Run this in a SEPARATE SSH window while run_all.sh is running.
# Usage: bash ~/binder_design/monitor.sh
# ================================================================

LOG="$HOME/rbx1_binder_design/binder_design.log"
OUTPUTS="$HOME/rbx1_binder_design/outputs"

# ANSI colours
GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"
CYAN="\033[36m"; BOLD="\033[1m"; RESET="\033[0m"
TICK="${GREEN}✓${RESET}"; SPIN=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")

step_done() { grep -q "$1" "$LOG" 2>/dev/null; }

spinner_idx=0
while true; do
    clear
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${BOLD}${CYAN}  RBX1 Binder Design — Live Progress Monitor${RESET}"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""

    # ── Step status ──────────────────────────────────────────────
    STEPS=(
        "STEP 1: Target Preparation"
        "Arm 1 complete"
        "Arm 2 (RFdiffusion) complete"
        "All background arms complete"
        "Merge complete"
        "Chai-1 complete"
        "Filter & rank complete"
        "Submission files ready"
    )
    LABELS=(
        "1  Target Prep (2LGV download)"
        "2  BindCraft (GPU, ~3h)"
        "3  RFdiffusion + CPU arms (ARM 2+3+5)"
        "3b CPU arms (PepPrCLIP + ESM3) done"
        "4  Merge candidates"
        "5  Chai-1 cross-validation (GPU)"
        "6  Filter & rank (BLAST)"
        "7  Submission files"
    )
    DONE_COUNT=0
    CURRENT_STEP=""

    for i in "${!STEPS[@]}"; do
        if step_done "${STEPS[$i]}"; then
            echo -e "   ${TICK} ${LABELS[$i]}"
            DONE_COUNT=$((DONE_COUNT+1))
        else
            SP="${SPIN[$((spinner_idx % ${#SPIN[@]}))]}"
            if [ -z "$CURRENT_STEP" ]; then
                echo -e "   ${YELLOW}${SP}${RESET} ${YELLOW}${LABELS[$i]}${RESET}  ← running"
                CURRENT_STEP="${LABELS[$i]}"
            else
                echo -e "   ${RED}◦${RESET} ${LABELS[$i]}"
            fi
        fi
    done

    # ── ETA bar ──────────────────────────────────────────────────
    TOTAL=8
    PCT=$((DONE_COUNT * 100 / TOTAL))
    FILLED=$((DONE_COUNT * 30 / TOTAL))
    BAR=$(printf "%${FILLED}s" | tr ' ' '█')$(printf "%$((30-FILLED))s" | tr ' ' '░')
    echo ""
    echo -e "   Progress: [${GREEN}${BAR}${RESET}] ${BOLD}${PCT}%%${RESET} (${DONE_COUNT}/${TOTAL} steps)"

    # ── Output file count ─────────────────────────────────────────
    echo ""
    BINDCRAFT_OUT=$(ls "$OUTPUTS/arm1_bindcraft/" 2>/dev/null | wc -l)
    CHAI_OUT=$(grep -c "pTM=" "$OUTPUTS/chai1_scores.csv" 2>/dev/null || echo 0)
    FINAL_OUT=$(grep -c "^rank" "$OUTPUTS/submission.csv" 2>/dev/null || echo 0)

    echo -e "   ${CYAN}Designs so far:${RESET}"
    echo -e "     BindCraft outputs  : ${BOLD}${BINDCRAFT_OUT}${RESET} files"
    echo -e "     Chai-1 scored      : ${BOLD}${CHAI_OUT}${RESET} sequences"
    echo -e "     Final submission   : ${BOLD}${FINAL_OUT}${RESET} / 100 sequences"

    # ── Last log lines ────────────────────────────────────────────
    echo ""
    echo -e "   ${CYAN}Last log lines:${RESET}"
    tail -n 5 "$LOG" 2>/dev/null | while IFS= read -r line; do
        echo -e "     ${line}"
    done

    echo ""
    echo -e "   ${RESET}Refreshing every 30s — Ctrl+C to exit"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

    spinner_idx=$((spinner_idx+1))
    sleep 30
done
