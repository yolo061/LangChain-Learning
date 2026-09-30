"""发送系统模板提示词"""
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from .model import get_llm
from .profile import profile
from langchain.agents.middleware import dynamic_prompt

from .prompts_template import agent_system_prompt, prompt_instructions
from .tools import get_tools


@dynamic_prompt
def get_prompt(state):
    return SystemMessage(
        content=agent_system_prompt.format(
            instructions=prompt_instructions["agent_instructions"],
            **profile
        )
    )

def get_agent():
    return create_agent(
        get_llm(),
        tools=get_tools(),
        middleware=[get_prompt],
    )