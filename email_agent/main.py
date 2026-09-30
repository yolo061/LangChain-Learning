from time import sleep

from agent.graph import build_graph
from agent.agent import get_agent
from agent.tools import set_current_email
from email_agent.server.connect import list_inbox, to_email_input
# from agent.prompts_template import email_input_1, email_input_2

def main():
    # 创建agent
    agent = get_agent()
    agent = build_graph(agent)

    # 绘制图像
    # draw_graph(agent)

    msg = list_inbox(top=3) # 拉取最近三条
    for i , m in enumerate(msg):
        print(i, m["subject"])

    pick = int(input("请输入处理邮件的序号:"))
    email_input = to_email_input(msg[pick])

    set_current_email(email_input)  # ← 关键新增
    response = agent.invoke({"email_input": email_input})

    # 打印处理结果
    for m in response["messages"]:
        m.pretty_print()


while(1):
    main()
    sleep(100000000)