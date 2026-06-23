from __future__ import annotations

from typing import Dict, List, Any

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoModelForMultimodalLM,
    AutoProcessor,
    AutoTokenizer,
)

from src.config import Config



class QwenLLM:
    """
    Supports:
    - Qwen2.5 text-only causal LMs
    - Qwen3.5 multimodal LMs in text-only mode
    - Full-precision BF16 inference for Qwen3.5-27B on H100
    - Qwen3.5 thinking mode with final-answer extraction
    """

    def __init__(self, config: Config):
        self.config = config
        self.model_name_lower = config.model_name.lower()
        self.is_qwen35 = "qwen3.5" in self.model_name_lower

        # H100 supports BF16 natively. Qwen3.5-27B is loaded without
        # 4-bit quantization so that the experiment uses the full BF16 model.
        if self.is_qwen35:
            torch_dtype: Any = torch.bfloat16
        elif config.dtype == "float16":
            torch_dtype = torch.float16
        elif config.dtype == "bfloat16":
            torch_dtype = torch.bfloat16
        else:
            torch_dtype = "auto"

        model_kwargs: Dict[str, Any] = {
            "device_map": config.device_map,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
            "dtype": torch_dtype,
        }

        if self.is_qwen35:
            # Qwen3.5 is released as an image-text-to-text / multimodal model,
            # but this project uses it with text-only inputs.
            self.processor = AutoProcessor.from_pretrained(
                config.model_name,
                trust_remote_code=True,
            )
            self.tokenizer = self.processor.tokenizer

            self.model = AutoModelForMultimodalLM.from_pretrained(
                config.model_name,
                **model_kwargs,
            )
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(
                config.model_name,
                trust_remote_code=True,
            )
            self.processor = None

            self.model = AutoModelForCausalLM.from_pretrained(
                config.model_name,
                **model_kwargs,
            )

        self.model.eval()

        print(
            f"[QwenLLM] model={config.model_name} "
            f"qwen3.5={self.is_qwen35} "
            f"dtype={torch_dtype} "
            f"thinking={self.is_qwen35}"
        )

        if hasattr(self.model, "get_memory_footprint"):
            footprint_gib = self.model.get_memory_footprint() / (1024 ** 3)
            print(f"[QwenLLM] model memory footprint: {footprint_gib:.2f} GiB")

    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        template_kwargs: Dict[str, Any] = {
            "tokenize": False,
            "add_generation_prompt": True,
        }

        # Keep Qwen2.5 unchanged. Enable thinking for Qwen3.5.
        if self.is_qwen35:
            template_kwargs["enable_thinking"] = True

        template_owner = self.processor if self.processor is not None else self.tokenizer

        return template_owner.apply_chat_template(
            messages,
            **template_kwargs,
        )

    def _prepare_inputs(self, text: str):
        if self.processor is not None:
            inputs = self.processor(
                text=[text],
                return_tensors="pt",
            )
        else:
            inputs = self.tokenizer(
                [text],
                return_tensors="pt",
            )

        # With device_map="auto", the input embedding normally lives on the
        # first CUDA device. model.device resolves to that device.
        return inputs.to(self.model.device)

    def generate(self, messages: List[Dict[str, str]]) -> str:
        text = self._build_prompt(messages)
        inputs = self._prepare_inputs(text)

        do_sample = self.config.temperature > 0

        max_new_tokens = self.config.max_new_tokens
        if self.is_qwen35:
            max_new_tokens = max(max_new_tokens, 512)

        generation_kwargs: Dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.eos_token_id,
        }

        if do_sample:
            generation_kwargs["temperature"] = self.config.temperature

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                **generation_kwargs,
            )

        prompt_length = inputs["input_ids"].shape[-1]
        new_tokens = output_ids[0][prompt_length:]

        decoded = self.tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        ).strip()

        # Qwen3.5 thinking mode may return:
        # <think>...</think> followed by the final answer.
        # Keep only the answer after the thinking block.
        if self.is_qwen35 and "</think>" in decoded:
            decoded = decoded.split("</think>", 1)[1].strip()

        return decoded
