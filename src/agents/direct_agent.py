# Author: mmj
# DATE: 30.05.2026
from src.prompts import DIRECT_PROMPT, BASE_SOLVER_INSTRUCTIONS
from src.agents.base import chat


class DirectAgent:
    name = "direct"

    def run(self, llm, question: str, answer_type: str = ""):
        prompt = DIRECT_PROMPT.format(
            question=question,
            base_instructions=BASE_SOLVER_INSTRUCTIONS,
        )
        answer = chat(llm, prompt)

        return {
            "agent": self.name,
            "final_output": answer,
            "trace": {
                "direct_prompt": prompt,
                "direct_answer": answer,
            },
        }
