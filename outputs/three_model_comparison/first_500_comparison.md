# HLE First-500 Comparison

All results are restricted to dataset indices `0–499`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 3.80% | 19 / 500 | 500/500 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Feedback | 5.20% | 26 / 500 | 500/500 | 20 | 13 | +7 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 5.00% | 25 / 500 | 500/500 | 9 | 3 | +6 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Oracle Feedback | 7.00% | 35 / 500 | 500/500 | 16 | 0 | +16 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Direct | 6.80% | 34 / 500 | 500/500 | — | — | — | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Feedback | 3.80% | 19 / 500 | 500/500 | 6 | 21 | -15 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Tool | 8.20% | 41 / 500 | 500/500 | 7 | 0 | +7 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Oracle Feedback | 12.40% | 62 / 500 | 500/500 | 28 | 0 | +28 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.40% | 27 / 500 | 500/500 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | Feedback | 2.00% | 10 / 500 | 500/500 | 7 | 24 | -17 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 6.80% | 34 / 500 | 500/500 | 7 | 0 | +7 | Complete |
| Qwen3.5-27B | NF4 4-bit | Oracle Feedback | 7.20% | 36 / 500 | 500/500 | 9 | 0 | +9 | Complete |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_500_results`
