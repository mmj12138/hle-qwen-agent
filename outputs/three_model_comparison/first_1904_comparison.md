# HLE First-1904 Comparison

All results are restricted to dataset indices `0–1903`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 4.99% | 95 / 1904 | 1904/1904 | — | — | — | Complete |
| Qwen3.5-0.8B | BF16/FP16 | XMaster-Feedback | 6.30% | 120 / 1904 | 1904/1904 | 72 | 47 | +25 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Tool | 5.78% | 110 / 1904 | 1904/1904 | 26 | 11 | +15 | Complete |
| Qwen3.5-0.8B | BF16/FP16 | Sim-XMaster | 6.06% | 111 / 1831 | 1831/1904 | 96 | 79 | +17 | Partial |
| Qwen3.5-9B | BF16/FP16 | Direct | 5.25% | 100 / 1904 | 1904/1904 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | XMaster-Feedback | 5.46% | 104 / 1904 | 1904/1904 | 51 | 47 | +4 | Complete |
| Qwen3.5-9B | BF16/FP16 | Tool | 5.88% | 112 / 1904 | 1904/1904 | 12 | 0 | +12 | Complete |
| Qwen3.5-9B | BF16/FP16 | Sim-XMaster | N/A | N/A | 0/1904 | N/A | N/A | N/A | N/A |
| Qwen3.5-27B | NF4 4-bit | Direct | 4.83% | 92 / 1904 | 1904/1904 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | XMaster-Feedback | 6.12% | 64 / 1046 | 1046/1904 | 38 | 24 | +14 | Partial |
| Qwen3.5-27B | NF4 4-bit | Tool | 5.88% | 112 / 1904 | 1904/1904 | 20 | 0 | +20 | Complete |
| Qwen3.5-27B | NF4 4-bit | Sim-XMaster | N/A | N/A | 0/1904 | N/A | N/A | N/A | N/A |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_1904_results`
