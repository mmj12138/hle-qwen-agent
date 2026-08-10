# HLE First-500 Comparison

All results are restricted to dataset indices `0–499`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 4.00% | 20 / 500 | 500/500 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | XMaster-Feedback | 4.80% | 24 / 500 | 500/500 | 18 | 14 | +4 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 5.20% | 26 / 500 | 500/500 | 9 | 3 | +6 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Sim-XMaster | 6.20% | 31 / 500 | 500/500 | 30 | 19 | +11 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 4.80% | 24 / 500 | 500/500 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | XMaster-Feedback | 4.80% | 24 / 500 | 500/500 | 12 | 12 | +0 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.40% | 32 / 500 | 500/500 | 8 | 0 | +8 | Complete |
| Qwen3.5-9B | BF16/FP16 | Sim-XMaster | 7.20% | 36 / 500 | 500/500 | 18 | 6 | +12 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.80% | 29 / 500 | 500/500 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | XMaster-Feedback | 5.80% | 29 / 500 | 500/500 | 14 | 14 | +0 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 7.40% | 37 / 500 | 500/500 | 8 | 0 | +8 | Complete |
| Qwen3.5-27B | NF4 4-bit | Sim-XMaster | N/A | N/A | 0/500 | N/A | N/A | N/A | N/A |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_500_results`
