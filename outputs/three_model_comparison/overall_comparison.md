# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-9B | direct | 0.0300 | 6 / 200 | -- | -- | -- |
| Qwen/Qwen3.5-9B | feedback | 0.0200 | 4 / 200 | 2 | 4 | -2 |
| Qwen/Qwen3.5-9B | tool | 0.0650 | 13 / 200 | 7 | 0 | +7 |
| Qwen/Qwen3.5-9B | tool_search | 0.0650 | 13 / 200 | 7 | 0 | +7 |
| Qwen/Qwen3.5-9B | oracle_feedback | 0.0450 | 9 / 200 | 3 | 0 | +3 |
| Qwen/Qwen3.5-9B | oracle_tool | 0.0800 | 16 / 200 | 10 | 0 | +10 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
