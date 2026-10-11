from __future__ import annotations

from typing import Any
from crewai.tools import tool


@tool("custom_tool_dummy")
def custom_tool_dummy(query: str = "") -> str:
    """
    사용자 정의 커스텀 도구 템플릿입니다.
    이 파일에 새로운 @tool 함수를 추가하거나 로직을 수정하면 별도의 서버 재시작 없이 즉시 반영됩니다.

    Args:
        query: 도구 실행에 필요한 입력 인자
    """
    return f"[Custom Tool Dummy Result] Query received: {query}"
