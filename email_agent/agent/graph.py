from pathlib import Path

from langgraph.graph import StateGraph, START

from .agent import get_agent
from .triage import State, triage_router

# 设置目录
PKG_ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = PKG_ROOT / "resources"
IMG_DIR.mkdir(parents=True, exist_ok=True)

def build_graph(response_agent, checkpointer=None):
    """组装大图：triage_router 分流，需要回复的进 response_agent。

    传入 checkpointer 后支持 write_email 工具内的 interrupt 人工确认。
    """
    graph = StateGraph(State)
    graph.add_node(triage_router)
    graph.add_node("response_agent", response_agent)
    graph.add_edge(START, "triage_router")

    return graph.compile(checkpointer=checkpointer)

def draw_graph(graph):
    """绘制拓扑图：notebook 里 display，同时落盘到 resources/graph.png。

    IPython 是 notebook 依赖，惰性导入保证纯脚本环境也能调用本模块。
    """
    try:
        from IPython.display import display, Image

        png = graph.get_graph(xray=True).draw_mermaid_png()
        display(Image(png))

        with open(IMG_DIR / "graph.png", "wb") as f:
            f.write(png)

        print("the graph successfully write")
    except Exception as e:
        print(f"the graph didn't write/generate successfully: {e}")
