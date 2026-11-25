"""该方法封装供agent调用的tool，在create_agent当中使用

人工确认方案：write_email 内部调用 langgraph 的 interrupt()，图执行到此处
暂停并等待人工决策；上层用 Command(resume="approve"/"reject") 恢复执行。
interrupt 所在的 tool 在 resume 后会被整体重新执行，此时 interrupt() 直接
返回 resume 值，不会再暂停。
"""
from langchain_core.tools import BaseTool, tool
from langgraph.types import interrupt

from email_agent.server.connect import create_reply_draft, send_draft


def get_tools(email_input: dict) -> list[BaseTool]:
    """工具集工厂：通过闭包把当前处理的邮件绑进 write_email，
    替代原先模块级 _current_email 全局注入。"""
    message_id = email_input["id"]

    @tool
    def write_email(to: str, subject: str, content: str) -> str:
        """Write a reply draft and ask the user for confirmation before sending."""
        decision = interrupt({
            "question": "确认发送这封回复吗?",
            "to": to,
            "subject": subject,
            "content": content,
        })
        if decision != "approve":
            return "User rejected this reply. Do not retry; wait for further instructions."

        draft = create_reply_draft(message_id, content)
        send_draft(draft["id"])
        return f"Reply sent to {to} with subject '{subject}'."

    @tool
    def schedule_meeting(
            attendees: list[str],
            subject: str,
            duration_minutes: int,
            preferred_day: str  # 日历会议
    ) -> str:
        """Schedule a calendar meeting."""
        return f"Meeting '{subject}' scheduled for {preferred_day} with {len(attendees)} attendees"

    @tool
    def check_calendar_availability(day: str) -> str:
        """Check calendar availability for a given day."""
        return f"Available times on {day}: 9:00 AM, 2:00 PM, 4:00 PM"

    return [write_email, schedule_meeting, check_calendar_availability]


if __name__ == '__main__':
    demo = {"id": "FAKE-ID"}
    for t in get_tools(demo):
        print(t.name, "->", list(t.args))
