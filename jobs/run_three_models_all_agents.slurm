#!/bin/bash
#SBATCH --job-name=hle_3models_all
#SBATCH --output=/storage/homefs/mj24z011/hle-qwen-agent/outputs/logs/%x_%j.out
#SBATCH --error=/storage/homefs/mj24z011/hle-qwen-agent/outputs/logs/%x_%j.err

#SBATCH --account=gratis
#SBATCH --partition=gpu
#SBATCH --qos=job_gratis
#SBATCH --gres=gpu:rtx4090:1
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G

set -euo pipefail

PROJECT_ROOT="/storage/homefs/mj24z011/hle-qwen-agent"
cd "${PROJECT_ROOT}"

module load Python/3.10
source "${HOME}/venvs/myddlenv/bin/activate"

python -m pip install -U "bitsandbytes>=0.46.1" accelerate

# Secrets only. Do not put API keys in the experiment shell script.
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

if [[ -f "${HOME}/.hle_search_env" ]]; then
    source "${HOME}/.hle_search_env"
fi

if [[ -z "${TAVILY_API_KEY:-}" ]]; then
    echo "ERROR: TAVILY_API_KEY is not configured."
    exit 1
fi

echo "============================================================"
echo "SLURM job started"
echo "Node         : $(hostname)"
echo "Start time   : $(date)"
echo "SLURM_JOB_ID : ${SLURM_JOB_ID:-none}"
echo "============================================================"

nvidia-smi || true

bash jobs/run_three_models_all_agents.sh

echo "============================================================"
echo "SLURM job finished"
echo "End time: $(date)"
echo "============================================================"
