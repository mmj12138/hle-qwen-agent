# HLE First-120 Comparison

All results are restricted to dataset indices `0–119`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 5.83% | 7 / 120 | 120/120 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | XMaster-Feedback | 4.17% | 5 / 120 | 120/120 | 3 | 5 | -2 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 9.17% | 11 / 120 | 120/120 | 5 | 1 | +4 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Sim-XMaster | 6.67% | 8 / 120 | 120/120 | 7 | 6 | +1 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 2.50% | 3 / 120 | 120/120 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | XMaster-Feedback | 1.67% | 2 / 120 | 120/120 | 1 | 2 | -1 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.67% | 8 / 120 | 120/120 | 5 | 0 | +5 | Complete |
| Qwen3.5-9B | BF16/FP16 | Sim-XMaster | 8.33% | 10 / 120 | 120/120 | 9 | 2 | +7 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 6.67% | 8 / 120 | 120/120 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | XMaster-Feedback | 6.67% | 8 / 120 | 120/120 | 4 | 4 | +0 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 10.00% | 12 / 120 | 120/120 | 4 | 0 | +4 | Complete |
| Qwen3.5-27B | NF4 4-bit | Sim-XMaster | 8.33% | 10 / 120 | 120/120 | 5 | 3 | +2 | Complete |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_120_results`
