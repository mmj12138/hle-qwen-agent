from dataclasses import dataclass
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


@dataclass
class Config:
    model_name: str = os.getenv("MODEL_NAME", "Qwen/Qwen3.5-27B")
    hle_split: str = os.getenv("HLE_SPLIT", "test")
    max_new_tokens: int = int(os.getenv("MAX_NEW_TOKENS", "512"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.0"))
    device_map: str = os.getenv("DEVICE_MAP", "auto")
    dtype: str = os.getenv("DTYPE", "auto")
    output_path: str = os.getenv("OUTPUT_PATH", "outputs/results.jsonl")


def get_config() -> Config:
    return Config()
