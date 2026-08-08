# HLE First-1500 Comparison

All results are restricted to dataset indices `0–1499`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 5.33% | 80 / 1500 | 1500/1500 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | XMaster-Feedback | 6.27% | 94 / 1500 | 1500/1500 | 57 | 43 | +14 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 6.33% | 95 / 1500 | 1500/1500 | 23 | 8 | +15 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Sim-XMaster | 6.13% | 92 / 1500 | 1500/1500 | 84 | 72 | +12 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 5.60% | 84 / 1500 | 1500/1500 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | XMaster-Feedback | 6.07% | 91 / 1500 | 1500/1500 | 47 | 40 | +7 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.40% | 96 / 1500 | 1500/1500 | 12 | 0 | +12 | Complete |
| Qwen3.5-9B | BF16/FP16 | Sim-XMaster | N/A | N/A | 0/1500 | N/A | N/A | N/A | N/A |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.00% | 75 / 1500 | 1500/1500 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | XMaster-Feedback | 6.12% | 64 / 1046 | 1046/1500 | 38 | 24 | +14 | Partial |
| Qwen3.5-27B | NF4 4-bit | Tool | 6.27% | 94 / 1500 | 1500/1500 | 19 | 0 | +19 | Complete |
| Qwen3.5-27B | NF4 4-bit | Sim-XMaster | N/A | N/A | 0/1500 | N/A | N/A | N/A | N/A |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_1500_results`
