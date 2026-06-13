# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-0.8B | direct | 0.0500 | 1 / 20 | -- | -- | -- |
| Qwen/Qwen3.5-0.8B | feedback | 0.0500 | 1 / 20 | 0 | 0 | +0 |
| Qwen/Qwen3.5-0.8B | tool | 0.0500 | 1 / 20 | 0 | 0 | +0 |
| Qwen/Qwen3.5-0.8B | tool_search | 0.0500 | 1 / 20 | 0 | 0 | +0 |
| Qwen/Qwen3.5-0.8B | oracle_feedback | 0.0500 | 1 / 20 | 0 | 0 | +0 |
| Qwen/Qwen3.5-0.8B | oracle_tool | 0.0500 | 1 / 20 | 0 | 0 | +0 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
