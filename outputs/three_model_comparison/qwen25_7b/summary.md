# Results for `Qwen/Qwen2.5-7B-Instruct`

| Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |
|---|---:|---:|---:|---:|---:|
| direct | 0.0488 | 93 / 1904 | -- | -- | -- |
| feedback | 0.0362 | 69 / 1904 | 26 | 50 | -24 |
| tool | 0.0515 | 98 / 1904 | 6 | 1 | +5 |
| tool_search | 0.0572 | 109 / 1904 | 42 | 26 | +16 |
| oracle_feedback | 0.1145 | 218 / 1904 | 125 | 0 | +125 |
| oracle_tool | 0.1161 | 221 / 1904 | 129 | 1 | +128 |
