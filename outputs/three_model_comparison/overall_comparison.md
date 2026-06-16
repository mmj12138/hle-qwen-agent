# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-27B | direct | 0.0523 | 68 / 1300 | -- | -- | -- |
| Qwen/Qwen3.5-27B | feedback | 0.0250 | 5 / 200 | 4 | 6 | -2 |
| Qwen/Qwen3.5-27B | tool | 0.0650 | 13 / 200 | 6 | 0 | +6 |
| Qwen/Qwen3.5-27B | tool_search | 0.0700 | 14 / 200 | 7 | 0 | +7 |
| Qwen/Qwen3.5-27B | oracle_feedback | 0.0550 | 11 / 200 | 4 | 0 | +4 |
| Qwen/Qwen3.5-27B | oracle_tool | 0.0850 | 17 / 200 | 10 | 0 | +10 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
