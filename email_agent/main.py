from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from email_agent.agent.agent import get_agent
from email_agent.agent.graph import build_graph
from email_agent.server.connect import list_inbox, to_email_input


def ask_approval(payload: dict) -> str:
    """终端侧的人工审批：展示 interrupt 抛出的草稿内容，返回 approve/reject"""
    print("\n" + "=" * 20, "待确认回复草稿 (interrupt)", "=" * 20)
    print(f"To: {payload['to']}")
    print(f"Subject: {payload['subject']}")
    print(payload["content"])
    answer = input("确认发送这封回复吗? (y/n): ").strip().lower()
    return "approve" if answer == "y" else "reject"


def run_graph(graph, config, email_input: dict) -> dict:
    """执行到 write_email 的 interrupt 处暂停，人工确认后 Command(resume=...) 恢复"""
    result = graph.invoke({"email_input": email_input}, config)
    while "__interrupt__" in result:
        decision = ask_approval(result["__interrupt__"][0].value)
        result = graph.invoke(Command(resume=decision), config)
    return result


def main():
    msg = list_inbox(top=3)  # 拉取最近三条
    for i, m in enumerate(msg):
        print(i, m["subject"])

    pick = int(input("请输入处理邮件的序号:"))
    email_input = to_email_input(msg[pick])

    graph = build_graph(get_agent(email_input), checkpointer=MemorySaver())
    # thread_id 定位本次会话的检查点，interrupt 暂停/恢复都靠它找到现场
    config = {"configurable": {"thread_id": f"email-{email_input['id']}"}}

    result = run_graph(graph, config, email_input)

    for m in result["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    while True:
        main()
        again = input("\n继续处理下一封邮件吗? (y/n): ").strip().lower()
        if again != "y":
            break
