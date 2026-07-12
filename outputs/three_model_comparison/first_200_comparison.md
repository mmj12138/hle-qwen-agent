# HLE First-200 Comparison

All results are restricted to dataset indices `0–199`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 4.50% | 9 / 200 | 200/200 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Feedback | 7.00% | 14 / 200 | 200/200 | 11 | 6 | +5 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 7.50% | 15 / 200 | 200/200 | 7 | 1 | +6 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Oracle Feedback | 8.50% | 17 / 200 | 200/200 | 8 | 0 | +8 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Direct | 8.00% | 16 / 200 | 200/200 | — | — | — | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Feedback | 4.50% | 9 / 200 | 200/200 | 2 | 9 | -7 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Tool | 11.50% | 23 / 200 | 200/200 | 7 | 0 | +7 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Oracle Feedback | 13.00% | 26 / 200 | 200/200 | 10 | 0 | +10 | Complete |
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
