from __future__ import annotations

from typing import Any, Dict, List

import torch
from transformers import AutoModelForMultimodalLM, AutoProcessor

from src.config import Config


class QwenLLM:
    """
    Simple Qwen3.5 text-only inference wrapper.

    - Uses one loading path for all Qwen3.5 model sizes
    - Loads the model in BF16
    - Disables thinking
    - Uses deterministic greedy decoding
    - Stores generation diagnostics for each model call
    """

    def __init__(self, config: Config):
        self.config = config
        self.thinking_enabled = False
        self.torch_dtype = torch.bfloat16
        self._generation_diagnostics: List[Dict[str, Any]] = []

        self.processor = AutoProcessor.from_pretrained(
            config.model_name,
            trust_remote_code=True,
        )
        self.tokenizer = self.processor.tokenizer

        model_kwargs: Dict[str, Any] = {
            "device_map": config.device_map,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
            "dtype": self.torch_dtype,
        }

        self.model = AutoModelForMultimodalLM.from_pretrained(
            config.model_name,
            **model_kwargs,
        )
        self.model.eval()

        print(
            f"[QwenLLM] model={config.model_name} "
            f"dtype={self.torch_dtype} "
            f"thinking={self.thinking_enabled}"
        )

        if hasattr(self.model, "get_memory_footprint"):
            footprint_gib = self.model.get_memory_footprint() / (1024 ** 3)
            print(f"[QwenLLM] model memory footprint: {footprint_gib:.2f} GiB")

    def reset_generation_diagnostics(self) -> None:
        """Clear diagnostics before starting a new benchmark sample."""
        self._generation_diagnostics.clear()

    def get_generation_diagnostics(
        self,
        clear: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return diagnostics for model calls made since the last reset."""
        diagnostics = [dict(item) for item in self._generation_diagnostics]
        if clear:
            self._generation_diagnostics.clear()
        return diagnostics

    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        return self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

    def _prepare_inputs(self, text: str):
        inputs = self.processor(
            text=[text],
            return_tensors="pt",
        )
        return inputs.to(self.model.device)

    def generate(self, messages: List[Dict[str, str]]) -> str:
        text = self._build_prompt(messages)
        inputs = self._prepare_inputs(text)

        max_new_tokens = int(self.config.max_new_tokens)

        generation_kwargs: Dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": False,
            "pad_token_id": self.tokenizer.eos_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                **generation_kwargs,
            )

        prompt_length = int(inputs["input_ids"].shape[-1])
        new_tokens = output_ids[0][prompt_length:]

        generated_token_count = int(new_tokens.shape[-1])
        reached_token_limit = generated_token_count >= max_new_tokens

        decoded = self.tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        ).strip()

        self._generation_diagnostics.append(
            {
                "call_index": len(self._generation_diagnostics),
                "prompt_tokens": prompt_length,
                "generated_tokens": generated_token_count,
                "max_new_tokens": max_new_tokens,
                "reached_token_limit": reached_token_limit,
                "output_empty": decoded == "",
            }
        )

        return decoded
