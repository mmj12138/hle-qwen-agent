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

Your task is to decide whether the current answer should be revised.

Important rules:
- Be conservative.
- Do NOT mark the answer as incorrect unless there is a clear and specific error.
- If the answer is plausible but you are not sure, output Status: uncertain.
- If the answer has the correct format and is not clearly contradicted by the question, output Status: correct.
- For expert-level math, science, medicine, law, history, or philosophy questions, do not overrule the answer unless you can identify a concrete mistake.
- Do not use the gold answer. You only have the question and the current answer.

Check:
1. Does the answer match the requested format?
2. For multiple-choice, is the answer one of the available options?
3. For exact-match, is the answer concise and in the expected form?
4. Is there a clear contradiction, arithmetic error, or reasoning error?
5. Is there enough evidence to justify changing the answer?

Output exactly two lines:
Status: correct OR incorrect OR uncertain
Feedback: <one short sentence explaining the status>
"""

FEEDBACK_REVISION_PROMPT = """You are the Revision Agent.

Revise the answer only based on the critic feedback.

Question:
{question}

Current answer:
{current_answer}

Critic feedback:
{feedback}

Important rules:
- Make the smallest necessary change.
- If the feedback only complains about format, only fix the format.
- Do not introduce unrelated reasoning.
- Do not change the answer unless the critic identified a concrete error.
- Do not mention the critic in the final answer.

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

ORACLE_REVISION_PROMPT = """You are the Revision Agent.

The previous answer was judged incorrect by an external evaluator.
The correct answer is NOT provided.

Question:
{question}

Previous answer:
{current_answer}

Answer type:
{answer_type}

Revise your answer.

Important rules:
- The previous answer is incorrect.
- Do not repeat the same final answer.
- Reconsider the problem from scratch.
- For multiple-choice questions, choose a different option only if you can justify it.
- For exact-match questions, output a concise answer.
- Do not mention the evaluator or oracle in the final answer.

{base_instructions}
"""

SEARCH_ROUTER_PROMPT = """You are a search-routing agent for a difficult QA benchmark.

Question:
{question}

Dataset category (auxiliary metadata only):
{category}

Decide whether web search is likely to provide useful external evidence.

Use search when the question depends on specific factual, scientific, historical,
literary, legal, biographical, bibliographic, or other domain knowledge that may
not be reliably solved from reasoning alone.

Do not use search when:
- the answer can be derived entirely from information in the question;
- it is a self-contained mathematical, logical, symbolic, or coding problem;
- a deterministic local tool is more appropriate;
- search is unlikely to produce evidence relevant to the exact question.

Generate a concise query that searches for the underlying fact or concept.
Do not copy the complete benchmark question into the query.
Do not search for phrases such as "HLE answer", "benchmark answer", or
"correct answer".

Return only one JSON object:
{{
  "use_search": true,
  "reason": "short reason",
  "search_query": "concise search query"
}}

If search is unnecessary:
{{
  "use_search": false,
  "reason": "short reason",
  "search_query": ""
}}
"""


SEARCH_SOLVER_PROMPT = """You are a search-augmented solver.

Question:
{question}

Dataset category:
{category}

Web search evidence:
{search_evidence}

Instructions:
- Use the evidence only when it is relevant to the question.
- Search snippets can be incomplete or misleading; reconcile multiple results.
- Do not claim that a fact is supported if the evidence does not contain it.
- Never mention benchmark answers, gold answers, the router, or internal tools.
- For multiple-choice questions, end with: Final Answer: <letter>
- For exact or short-answer questions, end with: Final Answer: <concise answer>

{base_instructions}
"""