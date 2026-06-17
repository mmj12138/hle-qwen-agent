# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-27B | direct | 0.0523 | 68 / 1300 | -- | -- | -- |
| Qwen/Qwen3.5-27B | feedback | 0.0200 | 20 / 1000 | 15 | 46 | -31 |
| Qwen/Qwen3.5-27B | tool | 0.0590 | 59 / 1000 | 8 | 0 | +8 |
| Qwen/Qwen3.5-27B | tool_search | 0.0600 | 60 / 1000 | 9 | 0 | +9 |
| Qwen/Qwen3.5-27B | oracle_feedback | 0.0750 | 75 / 1000 | 24 | 0 | +24 |
| Qwen/Qwen3.5-27B | oracle_tool | 0.0830 | 83 / 1000 | 32 | 0 | +32 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
