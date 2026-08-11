# HLE First-600 Comparison

All results are restricted to dataset indices `0–599`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 4.67% | 28 / 600 | 600/600 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | XMaster-Feedback | 5.33% | 32 / 600 | 600/600 | 22 | 18 | +4 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 5.50% | 33 / 600 | 600/600 | 9 | 4 | +5 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Sim-XMaster | 6.17% | 37 / 600 | 600/600 | 36 | 27 | +9 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 5.00% | 30 / 600 | 600/600 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | XMaster-Feedback | 5.33% | 32 / 600 | 600/600 | 18 | 16 | +2 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.33% | 38 / 600 | 600/600 | 8 | 0 | +8 | Complete |
| Qwen3.5-9B | BF16/FP16 | Sim-XMaster | 7.17% | 43 / 600 | 600/600 | 21 | 8 | +13 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.67% | 34 / 600 | 600/600 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | XMaster-Feedback | 6.00% | 36 / 600 | 600/600 | 19 | 17 | +2 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 7.00% | 42 / 600 | 600/600 | 8 | 0 | +8 | Complete |
| Qwen3.5-27B | NF4 4-bit | Sim-XMaster | 6.17% | 37 / 600 | 600/600 | 12 | 9 | +3 | Complete |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_600_results`
