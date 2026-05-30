# Author: mmj
# DATE: 30.05.2026
from src.prompts import SYSTEM_PROMPT


def chat(llm, user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    return llm.generate(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
