# Author: mmj
# DATE: 30.05.2026

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset_hle import load_hle_dataset

data = load_hle_dataset(split="test", limit=5)

for i, item in enumerate(data):
    print("=" * 80)
    print("index:", i)
    print("question:", item["question"][:100])
    print("image type:", type(item.get("image")))
    print("image value:", item.get("image"))
    print("image_preview type:", type(item.get("image_preview")))
    print("image_preview value:", item.get("image_preview"))
    print("rationale_image type:", type(item.get("rationale_image")))
    print("rationale_image value:", item.get("rationale_image"))
