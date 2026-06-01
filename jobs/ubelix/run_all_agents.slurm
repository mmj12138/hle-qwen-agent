#!/bin/bash
#SBATCH --job-name=hle_agent_all
#SBATCH --output=outputs/logs/%x_%j.out
#SBATCH --error=outputs/logs/%x_%j.err

#SBATCH --account=gratis
#SBATCH --partition=gpu
#SBATCH --qos=job_gratis
#SBATCH --gres=gpu:rtx4090:1

#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G

set -euo pipefail

PROJECT_ROOT="/storage/homefs/mj24z011/hle-qwen-agent"
cd "${PROJECT_ROOT}"

mkdir -p outputs/logs

module load Python/3.10
source ~/venvs/myddlenv/bin/activate

#pip install -r requirements.txt
#pip install pillow

set -a
source .env
set +a
echo "HF_TOKEN is set: ${HF_TOKEN:+yes}"

echo "============================================================"
echo "Ubelix job started"
echo "Node: $(hostname)"
echo "Python: $(which python)"
echo "Start time: $(date)"
echo "SLURM_JOB_ID: ${SLURM_JOB_ID:-none}"
echo "============================================================"

bash jobs/run_all_agents.sh

echo "============================================================"
echo "Ubelix job finished"
echo "End time: $(date)"
echo "============================================================"
