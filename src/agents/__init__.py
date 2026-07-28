from src.agents.direct_agent import DirectAgent
from src.agents.feedback_agent import FeedbackAgent
from src.agents.tool_agent import ToolAgent
from src.agents.oracle_feedback_agent import OracleFeedbackAgent
from src.agents.strong_feedback_agent import StrongFeedbackAgent
from src.agents.oracle_tool_agent import OracleToolAgent
from src.agents.tool_search_agent import ToolSearchAgent
from src.agents.xmaster_feedback_agent import XMasterFeedbackAgent


def get_agent(agent_name: str, max_iterations: int = 2):
    agent_name = agent_name.lower()

    if agent_name == "direct":
        return DirectAgent()

    if agent_name == "feedback":
        return FeedbackAgent(max_iterations=max_iterations)

    if agent_name == "tool":
        return ToolAgent(max_iterations=max_iterations)

    elif agent_name == "oracle_feedback":
        return OracleFeedbackAgent(max_iterations=max_iterations)

    elif agent_name == "strong_feedback":
        return StrongFeedbackAgent(max_iterations=max_iterations)

    elif agent_name == "oracle_tool":
        return OracleToolAgent(max_iterations=max_iterations)

    elif agent_name == "tool_search":
        return ToolSearchAgent(max_iterations=max_iterations)

    elif agent_name == "xmaster_feedback":
        return XMasterFeedbackAgent(num_candidates=max_iterations)

    raise ValueError(f"Unknown agent: {agent_name}")