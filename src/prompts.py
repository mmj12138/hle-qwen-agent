SYSTEM_PROMPT = """You are a careful reasoning agent for difficult benchmark questions.
You must answer accurately and follow the required output format.
Do not invent facts.
"""

BASE_SOLVER_INSTRUCTIONS = """Instructions:
- Read the question carefully.
- Identify whether the question is multiple-choice or exact-match.
- For multiple-choice questions, choose the best option and output only the option letter.
- For exact-match questions, output the concise final answer.
- Do not include explanation in the final line.
- End with exactly this format:
Final Answer: <answer>
"""

DIRECT_PROMPT = """You are the Solver Agent.

Solve the following HLE benchmark question.

Question:
{question}

{base_instructions}
"""

FEEDBACK_SOLVER_PROMPT = """You are the Solver Agent.

Solve the following HLE benchmark question and provide an initial answer.

Question:
{question}

{base_instructions}

End with exactly this format:
Initial Answer: <answer>
"""

FEEDBACK_CRITIC_PROMPT = """You are the Critic Agent.

Review the solver's current answer for the following HLE benchmark question.

Question:
{question}

Current answer:
{current_answer}

Check:
1. Does the answer match the question type?
2. For multiple-choice, is the selected option consistent with the question?
3. For exact-match, is the answer concise and in the expected form?
4. Are there obvious reasoning, factual, or calculation errors?
5. Is the solver overconfident despite missing information?

Output exactly two lines:
Status: correct OR incorrect
Feedback: <short feedback>
"""

FEEDBACK_REVISION_PROMPT = """You are the Solver Agent.

Revise your answer using the critic feedback.

Question:
{question}

Current answer:
{current_answer}

Critic feedback:
{feedback}

{base_instructions}
"""

TOOL_PLANNER_PROMPT = """You are a Tool-Planning Agent.

Question:
{question}

Available tools:
- calculator: useful for arithmetic expressions.
- rot13: useful when the question asks to apply ROT13 to a letter or string.
- mass_compare: useful when the question asks whether one celestial body is closer in mass to another.
- answer_format_hint: useful for avoiding output-format mistakes.
- domain_hint: useful for identifying the broad domain.
- no_tool: use if no tool is needed.

Decide which tools are useful.
Return a JSON object only.

Examples:
{{"tools": ["calculator"], "calculator_expression": "2+2"}}
{{"tools": ["rot13"], "rot13_text": "r"}}
{{"tools": ["mass_compare"], "target": "Mars", "body_a": "Earth", "body_b": "Moon"}}
{{"tools": ["answer_format_hint"]}}
{{"tools": ["domain_hint"]}}
{{"tools": ["no_tool"]}}

Important:
- Do not invent a calculator expression if the question is not arithmetic.
- Use rot13 only when the question explicitly mentions ROT13.
- Use mass_compare only when the question explicitly asks about relative masses.
- Use answer_format_hint when the question is exact-match or multiple-choice.
"""

TOOL_SOLVER_PROMPT = """You are the Solver Agent.

Solve the following HLE benchmark question.

Question:
{question}

Tool results:
{tool_results}

Previous verifier feedback:
{verifier_feedback}

Important rules:
- Tool results are optional evidence, not final answers.
- Use tool results only when they are directly relevant to the question.
- If the tool result is only an answer-format hint, solve normally and do not change your reasoning just because of the tool.
- Do not mention tool usage in the final answer.

{base_instructions}
"""

TOOL_VERIFIER_PROMPT = """You are the Verifier Agent.

Question:
{question}

Candidate answer:
{candidate_answer}

Tool results:
{tool_results}

Your job is to check whether the candidate answer is clearly contradicted by the tool results.

Important rules:
- Be conservative.
- Only mark incorrect if the candidate answer clearly conflicts with a real tool result.
- If the tool result is only an answer-format hint, do not change the answer.
- If the tool result is not directly relevant, keep the candidate answer.
- Do not change the answer unless the tool result provides clear evidence.

Output exactly two lines:
Status: correct OR incorrect
Final Answer: <answer>
"""