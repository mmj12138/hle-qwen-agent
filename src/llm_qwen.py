from __future__ import annotations

import os
from typing import Dict, List, Any

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoModelForMultimodalLM,
    AutoProcessor,
    AutoTokenizer,
    BitsAndBytesConfig,
)

from src.config import Config


def _env_flag(name: str, default: str = "auto") -> str:
    return os.getenv(name, default).strip().lower()


class QwenLLM:
    """
    Supports:
    - Qwen2.5 text-only causal LMs
    - Qwen3.5 multimodal LMs in text-only mode
    - Automatic NF4 4-bit loading for Qwen3.5-27B

    Environment controls:
    - LOAD_IN_4BIT=auto   -> quantize only models whose name contains "27b"
    - LOAD_IN_4BIT=1      -> force 4-bit
    - LOAD_IN_4BIT=0      -> disable 4-bit
    """

    def __init__(self, config: Config):
        self.config = config
        self.model_name_lower = config.model_name.lower()
        self.is_qwen35 = "qwen3.5" in self.model_name_lower

        quantize_setting = _env_flag("LOAD_IN_4BIT", "auto")
        if quantize_setting in {"1", "true", "yes", "on"}:
            self.use_4bit = True
        elif quantize_setting in {"0", "false", "no", "off"}:
            self.use_4bit = False
        else:
            # Default: only quantize the 27B model.
            self.use_4bit = "27b" in self.model_name_lower

        torch_dtype: Any = "auto"
        if config.dtype == "float16":
            torch_dtype = torch.float16
        elif config.dtype == "bfloat16":
            torch_dtype = torch.bfloat16

        model_kwargs: Dict[str, Any] = {
            "device_map": config.device_map,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }

        if self.use_4bit:
            compute_dtype = (
                torch.bfloat16
                if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
                else torch.float16
            )

            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_use_double_quant=True,
            )
            # The non-quantized layers use this dtype.
            model_kwargs["dtype"] = compute_dtype
        else:
            model_kwargs["dtype"] = torch_dtype

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
            f"load_in_4bit={self.use_4bit}"
        )

        if hasattr(self.model, "get_memory_footprint"):
            footprint_gib = self.model.get_memory_footprint() / (1024 ** 3)
            print(f"[QwenLLM] model memory footprint: {footprint_gib:.2f} GiB")

    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        template_kwargs: Dict[str, Any] = {
            "tokenize": False,
            "add_generation_prompt": True,
        }

        # Keep Qwen2.5 unchanged. Disable thinking only for Qwen3.5.
        if self.is_qwen35:
            template_kwargs["enable_thinking"] = False

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

        generation_kwargs: Dict[str, Any] = {
            "max_new_tokens": self.config.max_new_tokens,
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

        return self.tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        ).strip()
