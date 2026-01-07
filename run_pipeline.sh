#!/bin/bash
# Hydra Pipeline Runner
# Usage: ./run_pipeline.sh [args]

set -euo pipefail  # Exit on error, undefined vars, pipe failures

PROJECT_DIR="/opt/diabetes/proxmox-basic-soc/"

# Detect Virtual Environment
if [ -f "${PROJECT_DIR}/venv/bin/python3" ]; then
    PYTHON="${PROJECT_DIR}/venv/bin/python3"
elif [ -f "${PROJECT_DIR}/.venv/bin/python3" ]; then
    PYTHON="${PROJECT_DIR}/.venv/bin/python3"
else
    PYTHON="/usr/bin/python3"
fi

LOG_DIR="${PROJECT_DIR}/proxmox_soc/logs/cron"
LOCK_FILE="/tmp/hydra_pipeline.lock"

mkdir -p "$LOG_DIR" # To ensure directory exists

cd "$PROJECT_DIR"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting: $*" >> "${LOG_DIR}/cron.log"
logger -t "hydra-pipeline" "Started: $*"

# Use flock to prevent overlapping runs
# -n = non-blocking (skip if locked)
# -E 0 = exit 0 if lock fails (don't treat as error)
set +e
flock -n -E 0 "$LOCK_FILE" $PYTHON -u -m proxmox_soc.hydra_orchestrator "$@" >> "${LOG_DIR}/pipeline.log" 2>&1
EXIT_CODE=$?
set -e

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Completed: $*" >> "${LOG_DIR}/cron.log"
    logger -t "hydra-pipeline" "Completed: $*"
else
    echo "[$TIMESTAMP] Failed (exit $EXIT_CODE): $*" >> "${LOG_DIR}/cron.log"
    logger -t "hydra-pipeline" "Failed (exit $EXIT_CODE): $*"
fi