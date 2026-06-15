# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-27B | direct | 0.0350 | 7 / 200 | -- | -- | -- |
| Qwen/Qwen3.5-27B | feedback | 0.0200 | 4 / 200 | 3 | 6 | -3 |
| Qwen/Qwen3.5-27B | tool | 0.0400 | 8 / 200 | 7 | 6 | +1 |
| Qwen/Qwen3.5-27B | tool_search | 0.0000 | 0 / 0 | 0 | 0 | +0 |
| Qwen/Qwen3.5-27B | oracle_feedback | 0.0695 | 13 / 187 | 13 | 7 | +6 |
| Qwen/Qwen3.5-27B | oracle_tool | 0.0000 | 0 / 0 | 0 | 0 | +0 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
