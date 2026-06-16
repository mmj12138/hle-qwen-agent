# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-0.8B | direct | 0.0473 | 90 / 1904 | -- | -- | -- |
| Qwen/Qwen3.5-0.8B | feedback | 0.0557 | 106 / 1904 | 61 | 45 | +16 |
| Qwen/Qwen3.5-0.8B | tool | 0.0530 | 101 / 1904 | 11 | 0 | +11 |
| Qwen/Qwen3.5-0.8B | tool_search | 0.0567 | 108 / 1904 | 24 | 6 | +18 |
| Qwen/Qwen3.5-0.8B | oracle_feedback | 0.0819 | 156 / 1904 | 66 | 0 | +66 |
| Qwen/Qwen3.5-0.8B | oracle_tool | 0.0872 | 166 / 1904 | 76 | 0 | +76 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
