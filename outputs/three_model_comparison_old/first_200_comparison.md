# HLE First-200 Comparison

All results are restricted to dataset indices `0–199`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 5.00% | 10 / 200 | 200/200 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Feedback | 6.50% | 13 / 200 | 200/200 | 9 | 6 | +3 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 8.50% | 17 / 200 | 200/200 | 8 | 1 | +7 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Oracle Feedback | 9.50% | 19 / 200 | 200/200 | 9 | 0 | +9 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 3.00% | 6 / 200 | 200/200 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | Feedback | 3.00% | 6 / 200 | 200/200 | 5 | 5 | +0 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.50% | 13 / 200 | 200/200 | 7 | 0 | +7 | Complete |
| Qwen3.5-9B | BF16/FP16 | Oracle Feedback | 6.50% | 13 / 200 | 200/200 | 7 | 0 | +7 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.50% | 11 / 200 | 200/200 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | Feedback | 3.00% | 6 / 200 | 200/200 | 4 | 9 | -5 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 8.50% | 17 / 200 | 200/200 | 6 | 0 | +6 | Complete |
| Qwen3.5-27B | NF4 4-bit | Oracle Feedback | 10.48% | 11 / 105 | 105/200 | 3 | 0 | +3 | Partial |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_200_results`
