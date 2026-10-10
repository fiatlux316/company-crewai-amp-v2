from __future__ import annotations

import httpx

def invoke_rag_chat(query: str, session_id: str) -> str:
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
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("content", str(data))
    except Exception as e:
        return f"Error communicating with RAG API: {str(e)}"
