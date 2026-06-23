# HLE First-1000 Comparison

All results are restricted to dataset indices `0–999`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 4.60% | 46 / 1000 | 1000/1000 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Feedback | 5.30% | 53 / 1000 | 1000/1000 | 30 | 23 | +7 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 5.30% | 53 / 1000 | 1000/1000 | 12 | 5 | +7 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Oracle Feedback | 7.80% | 78 / 1000 | 1000/1000 | 32 | 0 | +32 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Direct | 5.80% | 58 / 1000 | 1000/1000 | — | — | — | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Feedback | 3.80% | 38 / 1000 | 1000/1000 | 11 | 31 | -20 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Tool | 6.60% | 66 / 1000 | 1000/1000 | 8 | 0 | +8 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Oracle Feedback | 13.00% | 130 / 1000 | 1000/1000 | 72 | 0 | +72 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.10% | 51 / 1000 | 1000/1000 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | Feedback | 2.00% | 20 / 1000 | 1000/1000 | 15 | 46 | -31 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 6.00% | 60 / 1000 | 1000/1000 | 9 | 0 | +9 | Complete |
| Qwen3.5-27B | NF4 4-bit | Oracle Feedback | 7.50% | 75 / 1000 | 1000/1000 | 24 | 0 | +24 | Complete |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_1000_results`
