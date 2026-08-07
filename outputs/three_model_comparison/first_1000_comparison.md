# HLE First-1000 Comparison

All results are restricted to dataset indices `0–999`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 5.10% | 51 / 1000 | 1000/1000 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | XMaster-Feedback | 5.60% | 56 / 1000 | 1000/1000 | 36 | 31 | +5 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 5.60% | 56 / 1000 | 1000/1000 | 13 | 8 | +5 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Sim-XMaster | 5.80% | 58 / 1000 | 1000/1000 | 56 | 49 | +7 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 5.10% | 51 / 1000 | 1000/1000 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | XMaster-Feedback | 5.30% | 53 / 1000 | 1000/1000 | 28 | 26 | +2 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.00% | 60 / 1000 | 1000/1000 | 9 | 0 | +9 | Complete |
| Qwen3.5-9B | BF16/FP16 | Sim-XMaster | N/A | N/A | 0/1000 | N/A | N/A | N/A | N/A |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.00% | 50 / 1000 | 1000/1000 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | XMaster-Feedback | 6.20% | 62 / 1000 | 1000/1000 | 36 | 24 | +12 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 6.20% | 62 / 1000 | 1000/1000 | 12 | 0 | +12 | Complete |
| Qwen3.5-27B | NF4 4-bit | Sim-XMaster | N/A | N/A | 0/1000 | N/A | N/A | N/A | N/A |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_1000_results`
