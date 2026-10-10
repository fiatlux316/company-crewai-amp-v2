from __future__ import annotations
import sys

TOOL_METADATA = {
    'name': 'rag.search',
    'description': '사내 지식베이스(Knowledge Base)를 검색하여 질문에 대한 종합적인 답변을 제공합니다.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': '챗봇에게 물어볼 질문 내용'
            },
            'session_id': {
                'type': 'string',
                'description': '대화 문맥 유지를 위한 세션 ID (선택 사항)'
            }
        },
        'required': ['query']
    },
    'output_schema': {
        'type': 'string',
        'description': '챗봇의 답변 텍스트'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    async def rag_search(query: str, session_id: str = "mcp-default-session") -> str:
        rag_api = None
        try:
            from .base_api import rag_api as api
            rag_api = api
        except ImportError:
            print("Error: Could not import rag_api in rag_service.py", file=sys.stderr)
            return "Error: Could not import rag_api"

        return await rag_api.invoke_rag_chat(query, session_id)
