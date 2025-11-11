"""
CBT Coach Agent (coach_agent)

이 패키지는 LangGraph Agent Server 표준을 따르는
CBT(인지행동치료) 챗봇의 핵심 로직을 포함합니다.

메인 그래프(app)는 'agent.py' 모듈에 정의되어 있으며,
'langgraph.json'에 의해 직접 참조됩니다.
"""

# 이 파일은 coach_agent을 Python 패키지로 만들기 위해 필요합니다.
# 비어 있어도 정상 작동합니다.

from graph import graph

__all__ = ["graph"]
