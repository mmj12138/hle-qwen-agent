# HLE First-800 Comparison

All results are restricted to dataset indices `0–799`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 5.25% | 42 / 800 | 800/800 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | XMaster-Feedback | 5.88% | 47 / 800 | 800/800 | 29 | 24 | +5 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 6.00% | 48 / 800 | 800/800 | 11 | 5 | +6 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Sim-XMaster | 6.00% | 48 / 800 | 800/800 | 46 | 40 | +6 | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 5.50% | 44 / 800 | 800/800 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | XMaster-Feedback | 5.75% | 46 / 800 | 800/800 | 24 | 22 | +2 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 6.50% | 52 / 800 | 800/800 | 8 | 0 | +8 | Complete |
| Qwen3.5-9B | BF16/FP16 | Sim-XMaster | 6.75% | 54 / 800 | 800/800 | 23 | 13 | +10 | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 5.25% | 42 / 800 | 800/800 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | XMaster-Feedback | 6.50% | 52 / 800 | 800/800 | 29 | 19 | +10 | Complete |
| Qwen3.5-27B | NF4 4-bit | Tool | 6.50% | 52 / 800 | 800/800 | 10 | 0 | +10 | Complete |
| Qwen3.5-27B | NF4 4-bit | Sim-XMaster | 6.38% | 51 / 800 | 800/800 | 20 | 11 | +9 | Complete |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_800_results`
