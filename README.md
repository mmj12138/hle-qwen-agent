# HLE Qwen Agent Comparison Project

This is a small project for comparing three agent settings on the HLE benchmark:

1. **Direct Agent**: answer directly with one prompt.
2. **Feedback Agent**: answer first, then self-criticize and revise.
3. **Tool Agent**: decide whether to use simple tools, then answer with tool results.

The project is designed for a small HLE subset first, for example 10–100 samples, before running a larger experiment.

## Project structure

```text
hle_qwen_agent_project/
├── README.md
├── requirements.txt
├── .env.example
├── run_example.slurm
├── scripts/
│   ├── check_dataset.py
│   ├── run_agents.py
│   └── summarize_results.py
├── src/
│   ├── config.py
│   ├── dataset_hle.py
│   ├── prompts.py
│   ├── llm_qwen.py
│   ├── tools.py
│   ├── agents.py
│   └── evaluator.py
└── outputs/
    └── .gitkeep
```

## 1. Install

On Ubelix:

```bash
module load Python/3.10
python -m venv ~/venvs/hle-agent
source ~/venvs/hle-agent/bin/activate
pip install -r requirements.txt
```

## 2. Hugging Face login

HLE may require access approval on Hugging Face first.

```bash
huggingface-cli login
```

Then test the dataset:

```bash
python scripts/check_dataset.py --limit 3
```

## 3. Run a small experiment

Start with only 5 examples:

```bash
python scripts/run_agents.py --limit 5 --agent direct
python scripts/run_agents.py --limit 5 --agent feedback
python scripts/run_agents.py --limit 5 --agent tool
```

Summarize results:

```bash
python scripts/summarize_results.py --input outputs/results.jsonl
```

## 4. Model notes

The default model name is:

```text
Qwen/Qwen3.5-27B
```

For debugging, you can use a smaller Qwen model by setting:

```bash
export MODEL_NAME="Qwen/Qwen2.5-7B-Instruct"
```

For a 27B model on one RTX 4090, you will probably need 4-bit quantization or an inference server such as vLLM. This starter project uses `transformers` by default for simplicity.

## 5. Agent settings

### Direct Agent

```text
Question -> Qwen -> Final Answer
```

### Feedback Agent

```text
Question -> Solver -> Initial Answer
         -> Critic -> Feedback
         -> Solver -> Final Answer
```

### Tool Agent

```text
Question -> Planner
         -> Optional tool calls
         -> Solver with tool results
         -> Verifier
         -> Final Answer
```

The tools included here are intentionally simple:

- calculator for arithmetic expressions
- domain_hint for broad subject detection
- no_tool fallback

You can later replace them with stronger tools such as SymPy, web search, Wikipedia retrieval, or local RAG.
