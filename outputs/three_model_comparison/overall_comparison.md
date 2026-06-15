# Three-Model HLE Agent Comparison

| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-7B-Instruct | direct | 0.0551 | 105 / 1904 | -- | -- | -- |
| Qwen/Qwen2.5-7B-Instruct | feedback | 0.0362 | 69 / 1904 | 21 | 57 | -36 |
| Qwen/Qwen2.5-7B-Instruct | tool | 0.0604 | 115 / 1904 | 10 | 0 | +10 |
| Qwen/Qwen2.5-7B-Instruct | tool_search | 0.0609 | 116 / 1904 | 11 | 0 | +11 |
| Qwen/Qwen2.5-7B-Instruct | oracle_feedback | 0.1192 | 227 / 1904 | 122 | 0 | +122 |
| Qwen/Qwen2.5-7B-Instruct | oracle_tool | 0.1176 | 224 / 1904 | 121 | 2 | +119 |

## Notes

- `tool_search` uses Tavily web search after deterministic-tool routing.
- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.
- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.
