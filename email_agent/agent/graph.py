from langgraph.graph import StateGraph, START
from IPython.display import display, Image
from pathlib import Path

"""inner function"""
from .triage import triage_router
from .agent import create_agent
from .triage import State

# 设置目录
PKG_ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = PKG_ROOT / "resources"
IMG_DIR.mkdir(parents=True, exist_ok=True)

def build_graph(response_agent : create_agent):
    agent = StateGraph(State)
    # 添加路由分类
    agent : StateGraph = agent.add_node(triage_router)
    # 添加回复处理agent
    agent : StateGraph = agent.add_node("response_agent", response_agent)
    agent : StateGraph = agent.add_edge(START, "triage_router")

    return agent.compile()

def draw_graph(agent : build_graph):
    # 保存图片
    try :
        # 打印图片
        png = agent.get_graph(xray=True).draw_mermaid_png()
        display(Image(png))

        # 保存图片
        with open(IMG_DIR / "graph.png","wb") as graph:
            graph.write(png)

        print("the graph successfully write")
    except Exception as e:
        print(f"the graph didn't write/generate successfully: {e}")
