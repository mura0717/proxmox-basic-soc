#!/bin/bash
# Ensure we are in the right directory
cd /opt/diabetes/proxmox-basic-soc

# Activate venv if you use one
# source venv/bin/activate

# Run the orchestrator
# $@ passes arguments from cron (e.g., --nmap discovery) to python
/usr/bin/python3 proxmox_soc/orchestrator.py "$@" >> logs/cron_output.log 2>&1

# Discovery every 4 hours
0 */4 * * * /opt/diabetes/proxmox-basic-soc/run_pipeline.sh --nmap discovery

# MS365 Sync Daily at 6 AM
0 6 * * * /opt/diabetes/proxmox-basic-soc/run_pipeline.sh --ms365