# HLE First-200 Comparison

All results are restricted to dataset indices `0–199`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 6.50% | 13 / 200 | 200/200 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Feedback | 6.50% | 13 / 200 | 200/200 | 3 | 3 | +0 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 8.50% | 17 / 200 | 200/200 | 4 | 0 | +4 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool + Search | 5.00% | 1 / 20 | 20/200 | 0 | 0 | +0 | Partial |
| Qwen3.5-0.8B | BF16/FP16 | Oracle Feedback | 8.50% | 17 / 200 | 200/200 | 4 | 0 | +4 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Oracle Tool | 10.50% | 21 / 200 | 200/200 | 8 | 0 | +8 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Direct | 5.00% | 10 / 200 | 200/200 | — | — | — | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Feedback | 4.50% | 9 / 200 | 200/200 | 3 | 4 | -1 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Tool | 7.00% | 14 / 200 | 200/200 | 4 | 0 | +4 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Tool + Search | N/A | N/A | 0/200 | N/A | N/A | N/A | N/A |
| Qwen2.5-7B-Instruct | BF16/FP16 | Oracle Feedback | 11.50% | 23 / 200 | 200/200 | 13 | 0 | +13 | Complete |
| Qwen2.5-7B-Instruct | BF16/FP16 | Oracle Tool | 13.00% | 26 / 200 | 200/200 | 16 | 0 | +16 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 2.00% | 4 / 200 | 200/200 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | Feedback | 2.00% | 4 / 200 | 200/200 | 4 | 4 | +0 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 2.78% | 1 / 36 | 36/200 | 0 | 0 | +0 | Partial |
| Qwen3.5-27B | NF4 4-bit | Tool + Search | N/A | N/A | 0/200 | N/A | N/A | N/A | N/A |
| Qwen3.5-27B | NF4 4-bit | Oracle Feedback | N/A | N/A | 0/200 | N/A | N/A | N/A | N/A |
| Qwen3.5-27B | NF4 4-bit | Oracle Tool | N/A | N/A | 0/200 | N/A | N/A | N/A | N/A |

## Interpretation notes

- Only identical indices `0–199` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-27B uses NF4 4-bit quantization.
- `Tool + Search` may be available only for Qwen2.5-7B-Instruct; missing combinations are shown as `N/A`.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_200_results`
