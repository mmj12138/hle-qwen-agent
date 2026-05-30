from __future__ import annotations

from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from src.config import Config


class QwenLLM:
    def __init__(self, config: Config):
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_name, trust_remote_code=True)

        torch_dtype = "auto"
        if config.dtype == "float16":
            torch_dtype = torch.float16
        elif config.dtype == "bfloat16":
            torch_dtype = torch.bfloat16

        self.model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            torch_dtype=torch_dtype,
            device_map=config.device_map,
            trust_remote_code=True,
        )
        self.model.eval()

    def generate(self, messages: List[Dict[str, str]]) -> str:
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        do_sample = self.config.temperature > 0

        generation_kwargs = {
            "max_new_tokens": self.config.max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if do_sample:
            generation_kwargs["temperature"] = self.config.temperature

        with torch.no_grad():
            output_ids = self.model.generate(**inputs, **generation_kwargs)

        new_tokens = output_ids[0][inputs.input_ids.shape[-1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
