# HLE First-700 Comparison

All results are restricted to dataset indices `0–699`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 4.86% | 34 / 700 | 700/700 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | xmaster_feedback | 5.71% | 40 / 700 | 700/700 | 25 | 19 | +6 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 5.57% | 39 / 700 | 700/700 | 10 | 5 | +5 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 5.14% | 36 / 700 | 700/700 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | xmaster_feedback | 5.29% | 37 / 700 | 700/700 | 20 | 19 | +1 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.29% | 44 / 700 | 700/700 | 8 | 0 | +8 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.43% | 38 / 700 | 700/700 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | xmaster_feedback | 6.00% | 42 / 700 | 700/700 | 23 | 19 | +4 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 6.71% | 47 / 700 | 700/700 | 9 | 0 | +9 | Complete |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_700_results`
