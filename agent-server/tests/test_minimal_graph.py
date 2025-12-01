# test_minimal_graph.py

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver  # 임시 메모리용
from coach_agent.graph.state import State
from coach_agent.graph.weekly.builder import build_weekly_subgraph
from coach_agent.graph.general.builder import build_general_subgraph
from coach_agent.graph.main.builder import build_main_graph

def main():
    # 1. SubGraph들 빌드
    weekly_app = build_weekly_subgraph()
    general_app = build_general_subgraph()

    # 2. Checkpointer (메모리) + MainGraph 빌드
    checkpointer = MemorySaver()
    main_app = build_main_graph(weekly_app, general_app, checkpointer=checkpointer)

    # 3. 같은 thread_id로 여러 번 호출해보기
    config = {"configurable": {"thread_id": "test_thread_1"}}


    i = 0
    while True:
        i += 1
        # 첫 호출: session_type None -> WEEKLY로 초기화, GREETING 턴
        # 두 번째 호출: COUNSEL 턴
        # 여러 번 더 호출해보면, 어느 순간 WRAP_UP → EXIT → exit=True 로 바뀔 거야.        
        result = main_app.invoke(
            {"messages": [HumanMessage(content="안녕하세요")]},
            config=config,
        )
        print(f"=== {i}st turn ===")
        print("phase:", result["phase"], "exit:", result["exit"])
        print(result["messages"][-1].content)

        if result["exit"]:  # 정상 종료
            break
        if i > 10:
            break  # 무한 루프 방지용

if __name__ == "__main__":
    main()

