from __future__ import annotations

import httpx

async def invoke_rag_chat(query: str, session_id: str) -> str:
    """내부 RAG API로 챗봇 질의를 전송하고 답변을 받아옵니다."""
    url = "http://rag-api:8001/chat"
    payload = {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "uuid": session_id
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # RAG API의 응답 모델은 Turn(role, content) 형식입니다.
            return data.get("content", str(data))
    except Exception as e:
        return f"Error communicating with RAG API: {str(e)}"
