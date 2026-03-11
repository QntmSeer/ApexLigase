#!/bin/bash
# ================================================================
# run_all.sh — Optimised Master Orchestration for RBX1 Binders
#
# Execution strategy:
#   GPU arms (BindCraft, RFdiffusion, Chai-1) run sequentially to
#   prevent VRAM conflicts on the H100.
#   CPU arms (PepPrCLIP, ESM3) run concurrently with RFdiffusion
#   since they are IO/CPU-bound and don't compete for GPU memory.
#   BLAST novelty check uses 16 parallel threads (IO-bound).
# ================================================================
set -e

WORKDIR="$HOME/rbx1_binder_design"
LOG="$WORKDIR/binder_design.log"
SCRIPTS="$WORKDIR"
BG_PIDS=()

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
section() { echo "" | tee -a "$LOG"; echo "================================================================" | tee -a "$LOG"; log "$*"; echo "================================================================" | tee -a "$LOG"; }

# ----------------------------------------------------------------
# PUSH NOTIFICATIONS via ntfy.sh (free, no account needed)
# Subscribe on your phone: https://ntfy.sh  → subscribe to your topic
# Or: iOS/Android app "ntfy" → subscribe to: rbx1-binder-YOUR_TOPIC
# ----------------------------------------------------------------
NTFY_TOPIC="rbx1-binder-$(hostname | tr -dc 'a-z0-9' | head -c8)"
log "Push notification topic: https://ntfy.sh/$NTFY_TOPIC"
log "Subscribe now on your phone with the ntfy app!"

notify() {
    local TITLE="$1"
    local MSG="$2"
    local PRIORITY="${3:-default}"  # min/low/default/high/urgent
    curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
        -H "Title: $TITLE" \
        -H "Priority: $PRIORITY" \
        -H "Tags: dna" \
        -d "$MSG" > /dev/null 2>&1 || true  # never fail the pipeline if notify fails
    log "[NOTIFY] $TITLE — $MSG"
}

eval "$(conda shell.bash hook)"

section "RBX1 Binder Design Pipeline — START ($(date))"
mkdir -p "$WORKDIR/outputs"

# ----------------------------------------------------------------
# STEP 1: Prepare target (fast, ~30s, CPU only)
# ----------------------------------------------------------------
section "STEP 1: Target Preparation"
conda run -n bioutils python3 "$SCRIPTS/02_prep_target.py" 2>&1 | tee -a "$LOG"
log "Step 1 complete."
notify "✅ Step 1 Done" "Target prep complete. 2LGV downloaded, RING domain extracted." low

# ----------------------------------------------------------------
# STEP 2: GPU ARM 1 — BindCraft (~3h, H100 fully loaded)
# ----------------------------------------------------------------
section "STEP 2: ARM 1 — BindCraft (GPU, ~3h)"
bash "$SCRIPTS/arm1_bindcraft/run_bindcraft.sh" 2>&1 | tee -a "$LOG"
log "Arm 1 complete."
BC_COUNT=$(ls "$WORKDIR/outputs/arm1_bindcraft/" 2>/dev/null | wc -l)
notify "✅ BindCraft Done" "Arm 1 finished. ~${BC_COUNT} design files generated." high

# ----------------------------------------------------------------
# STEP 3: GPU ARM 2 — RFdiffusion (GPU, ~1h)
#          + CPU ARM 3 PepPrCLIP in background (CPU / small GPU)
#          + CPU ARM 5 ESM3 in background (CPU / small GPU)
# ----------------------------------------------------------------
section "STEP 3: ARM 2 (GPU RFdiffusion) + ARM 3 + ARM 5 in background"

# Start PepPrCLIP in background (CPU-light, ~20min)
conda run -n bioutils python3 "$SCRIPTS/arm3_pepprclip/run_pepprclip.py" \
    >> "$LOG" 2>&1 &
BG_PIDS+=($!)
log "  ARM 3 (PepPrCLIP) started in background [PID ${BG_PIDS[-1]}]"

# Start ESM3 in background (CPU/GPU-light, ~15min)
conda run -n esm3 python3 "$SCRIPTS/arm5_esm3/run_esm3_design.py" \
    >> "$LOG" 2>&1 &
BG_PIDS+=($!)
log "  ARM 5 (ESM3) started in background [PID ${BG_PIDS[-1]}]"

# Run RFdiffusion on GPU (foreground — needs full VRAM)
bash "$SCRIPTS/arm2_rfdiffusion/run_rfdiffusion.sh" 2>&1 | tee -a "$LOG"
log "Arm 2 (RFdiffusion) complete."

# Wait for background CPU arms to finish before proceeding
log "Waiting for background CPU arms (3, 5) to finish..."
for pid in "${BG_PIDS[@]}"; do
    wait "$pid" && log "  PID $pid finished OK" || log "  WARNING: PID $pid exited with error"
done
BG_PIDS=()
log "All background arms complete."
notify "✅ Arms 2+3+5 Done" "RFdiffusion + PepPrCLIP + ESM3 all complete. Merging candidates." default

# ----------------------------------------------------------------
# STEP 4: Merge → Chai-1 input (fast, ~10s)
# ----------------------------------------------------------------
section "STEP 4: Merge candidates for Chai-1"
conda run -n bioutils python3 "$SCRIPTS/filter_and_rank.py" --merge-only 2>&1 | tee -a "$LOG"
log "Merge complete."

# ----------------------------------------------------------------
# STEP 5: GPU ARM 4 — Chai-1 cross-validation (~1h, bfloat16 AMP)
# ----------------------------------------------------------------
section "STEP 5: ARM 4 — Chai-1 Cross-Validation (GPU, bfloat16 AMP)"
conda run -n chai1 python3 "$SCRIPTS/validate_chai1.py" 2>&1 | tee -a "$LOG"
log "Chai-1 complete."
CHAI_PASS=$(grep -c "passes_chai1.*True" "$WORKDIR/outputs/chai1_scores.csv" 2>/dev/null || echo "?")
notify "✅ Chai-1 Done" "Cross-validation complete. ${CHAI_PASS} sequences passed Chai-1 filter." high

# ----------------------------------------------------------------
# STEP 6: Filter, rank with parallel BLAST (16 threads)
# ----------------------------------------------------------------
section "STEP 6: Filter & Rank (parallel BLAST, ipSAE composite score)"
conda run -n bioutils python3 "$SCRIPTS/filter_and_rank.py" 2>&1 | tee -a "$LOG"
log "Filter & rank complete."

# ----------------------------------------------------------------
# STEP 7: Prepare submission
# ----------------------------------------------------------------
section "STEP 7: Prepare Submission Files"
conda run -n bioutils python3 "$SCRIPTS/prepare_submission.py" 2>&1 | tee -a "$LOG"
log "Submission files ready."

# ----------------------------------------------------------------
# DONE — notify and print topic reminder
# ----------------------------------------------------------------
SEQ_COUNT=$(grep -c "." "$WORKDIR/outputs/submission.csv" 2>/dev/null || echo 0)
SEQ_COUNT=$((SEQ_COUNT-1))  # subtract header
notify "🏁 Pipeline COMPLETE!" "${SEQ_COUNT}/100 sequences ready. Download: submission.csv" urgent

# ----------------------------------------------------------------
# DONE
# ----------------------------------------------------------------
section "ALL STEPS COMPLETE — $(date)"
log "Outputs  : $WORKDIR/outputs/"
log "Submit   : $WORKDIR/outputs/submission.csv"
log "Method   : $WORKDIR/outputs/method_description.txt"


