import sys
from pathlib import Path
import argparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_config
from src.dataset_hle import load_hle_dataset, normalize_hle_item, format_question
from src.data_utils import empty_image, is_text_only

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default=None)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Only inspect samples without image or rationale_image.",
    )
    parser.add_argument(
        "--show-samples",
        action="store_true",
        help="Print sample questions and gold answers.",
    )
    args = parser.parse_args()

    config = get_config()
    split = args.split or config.hle_split

    # Important:
    # Load full dataset first, then filter, then limit.
    # Otherwise the first few samples may all be image-based and filtering gives 0 samples.
    data = load_hle_dataset(
        split=split,
        limit=args.limit,
        text_only=args.text_only,
        export_path="outputs/hle_text_only.jsonl",
    )

    print("Dataset loaded successfully.")
    print("Original dataset size:", len(data))

    if args.text_only:
        data = data.filter(is_text_only)
        print("Text-only dataset size:", len(data))

    if args.limit is not None:
        data = data.select(range(min(args.limit, len(data))))

    print("Number of inspected samples:", len(data))

    if len(data) == 0:
        print("No samples available after filtering.")
        print("Try running without --text-only, or increase the dataset limit after filtering.")
        return

    print("Raw field names:", list(data[0].keys()))

    if not args.show_samples:
        print("Use --show-samples if you want to print sample questions and answers.")
        return

    for i, item in enumerate(data):
        ex = normalize_hle_item(dict(item))

        print("=" * 80)
        print(f"Sample {i}")
        print("Category:", ex["category"])
        print("Answer type:", ex["answer_type"])
        print("Question:")
        print(format_question(ex)[:1500])
        print("Gold answer:")
        print(ex["answer"])


if __name__ == "__main__":
    main()