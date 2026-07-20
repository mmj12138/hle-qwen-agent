# HLE First-1904 Comparison

All results are restricted to dataset indices `0–1903`.

| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.5-0.8B | BF16/FP16 | Direct | 4.99% | 95 / 1904 | 1904/1904 | — | — | — | Complete |
| Qwen3.5-9B | BF16/FP16 | Direct | 5.25% | 100 / 1904 | 1904/1904 | — | — | — | Complete |
| Qwen3.5-27B | NF4 4-bit | Direct | 4.83% | 92 / 1904 | 1904/1904 | — | — | — | Complete |

## Interpretation notes

- Only identical indices `0–99` are compared.
- `W→R` and `R→W` are computed against Direct on shared indices.
- A partial result is retained but marked as `Partial`.
- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.
- Qwen3.5-27B uses NF4 4-bit quantization.

Extracted subsets: `/Users/mmj/PycharmProjects/hle_qwen_agent_project/outputs/three_model_comparison/first_1904_results`
