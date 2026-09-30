from typing import Literal, TypedDict, Annotated

from langgraph_sdk.schema import Command
from pydantic import BaseModel, Field
from langgraph.graph import add_messages, END
from langgraph.types import Command

# 导入prompt模版库
from .prompts_template import triage_system_prompt, triage_user_prompt, prompt_instructions
from .profile import profile
from .model import get_llm # 相对导入



class Route(BaseModel):
    """Analyze the unread email and route it according to its content"""

    # 生成决策
    reasoning : str = Field(description="Step-by-Step reasoning behind the classification.")

    # 分类规范
    classification : Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email: ignore for irrelevant emails,notify for important information that doesn't need a response,respond for emails that need a reply",
    )

class State(TypedDict):
    email_input : str
    # 给message绑定一个add_message行为
    messages : Annotated[list, add_messages]

# 获取带结构化的输出
def get_llm_router():
    llm_router = get_llm().with_structured_output(Route)
    return llm_router

def triage_router(state : State) -> Command[
    Literal["response_agent","__end__"]
]:
    # load the profile
    author = state["email_input"]["author"]
    to = state["email_input"]["to"]
    subject = state["email_input"]
    email_thread = state["email_input"]["email_thread"]

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],  #
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
        examples=None
    )

    user_prompt = triage_user_prompt.format(
        author=author,
        to=to,
        subject=subject,
        email_thread=email_thread
    )

    # 创建系统提示词
    result = get_llm_router().invoke(
        [
            ("system", system_prompt),
            ("user", user_prompt)
        ]
    )

    if result.classification == "respond" :
        print("📧 Classification: RESPOND - This email requires a response")
        goto = "response_agent"

        update = {
            "messages" : [
                ("user", f"Respond to email {state['email_input']}")
            ]
        }
    elif result.classification == "ignore" :
        print("🚫 Classification: IGNORE - This email can be safely ignored")
        update = None # update字段的名称
        goto = END # 结束字段
    elif result.classification == "notify" :
        print("🔔 Classification: NOTIFY - This email contains important information")
        update = None
        goto = END
    else :
        raise ValueError(f"Invalid classification: {result.classification}")
    return Command(goto=goto, update=update) # 在本次处理结束后会自动将update，merge到State当中
