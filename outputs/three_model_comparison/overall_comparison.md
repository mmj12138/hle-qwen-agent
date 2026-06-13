# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-0.8B | direct | 0.0604 | 115 / 1904 | -- | -- | -- |
| Qwen/Qwen3.5-0.8B | feedback | 0.0562 | 107 / 1904 | 41 | 49 | -8 |
| Qwen/Qwen3.5-0.8B | tool | 0.0614 | 117 / 1904 | 4 | 2 | +2 |
| Qwen/Qwen3.5-0.8B | tool_search | 0.0500 | 1 / 20 | 0 | 0 | +0 |
| Qwen/Qwen3.5-0.8B | oracle_feedback | 0.0720 | 137 / 1904 | 22 | 0 | +22 |
| Qwen/Qwen3.5-0.8B | oracle_tool | 0.0730 | 139 / 1904 | 26 | 2 | +24 |
| Qwen/Qwen2.5-7B-Instruct | direct | 0.0488 | 93 / 1904 | -- | -- | -- |
| Qwen/Qwen2.5-7B-Instruct | feedback | 0.0362 | 69 / 1904 | 26 | 50 | -24 |
| Qwen/Qwen2.5-7B-Instruct | tool | 0.0515 | 98 / 1904 | 6 | 1 | +5 |
| Qwen/Qwen2.5-7B-Instruct | tool_search | 0.0000 | 0 / 0 | 0 | 0 | +0 |
| Qwen/Qwen2.5-7B-Instruct | oracle_feedback | 0.1145 | 218 / 1904 | 125 | 0 | +125 |
| Qwen/Qwen2.5-7B-Instruct | oracle_tool | 0.1161 | 221 / 1904 | 129 | 1 | +128 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
