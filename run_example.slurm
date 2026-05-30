#!/bin/bash
#SBATCH --job-name=hle_agent_test
#SBATCH --output=outputs/%x_%j.out
#SBATCH --error=outputs/%x_%j.err
#SBATCH --partition=gpu
#SBATCH --qos=job_gratis
#SBATCH --gres=gpu:rtx4090:1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00

set -euo pipefail

module load Python/3.10

source ~/venvs/hle-agent/bin/activate

# Optional:
# export MODEL_NAME="Qwen/Qwen3.5-27B"
# export MAX_NEW_TOKENS=512

python scripts/check_dataset.py --limit 3

python scripts/run_agents.py --agent direct --limit 5
python scripts/run_agents.py --agent feedback --limit 5
python scripts/run_agents.py --agent tool --limit 5

python scripts/summarize_results.py --input outputs/results.jsonl
