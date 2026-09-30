"""该方法封装供agent调用的tool，在create_agent当中使用"""
from email_agent.server.connect import create_reply_draft, send_draft
from langchain_core.tools import tool, StructuredTool

TOOL_REGISTRY = {}
_current_email : dict = {}

def set_current_email(email_input : dict):
    global _current_email
    _current_email = email_input

# register函数
def register(tool_fn : StructuredTool):
    TOOL_REGISTRY[tool_fn.name] = tool_fn
    return tool_fn

def get_tools():
    return list(TOOL_REGISTRY.values())

# 使用注册器将tool进行注册
@register
@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write a reply draft and ask the user for confirmation before sending."""
    print("\n" + "=" * 20, "待发送草稿", "=" * 20)
    print(f"To: {to}\nSubject: {subject}\n{content}")
    answer = input("确认发送这封回复吗? (y/n): ").strip().lower()
    if answer != "y":
        return "User rejected this reply. Do not retry; wait for further instructions."

    draft = create_reply_draft(_current_email["id"], content)   # ← 真建草稿
    send_draft(draft["id"])                                     # ← 真发送
    return f"Reply sent to {to} with subject '{subject}'."

@register
@tool
def schedule_meeting(
        attendees: list[str],
        subject: str,
        duration_minutes: int,
        preferred_day: str  # 日历会议
) -> str:
    """Schedule a calendar meeting."""
    return f"Meeting '{subject}' scheduled for {preferred_day} with {len(attendees)} attendees"

@register
@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability for a given day."""
    return f"Available times on {day}: 9:00 AM, 2:00 PM, 4:00 PM"

if __name__ == '__main__':
    for t in get_tools():
        print(t.name, "->", list(t.args))