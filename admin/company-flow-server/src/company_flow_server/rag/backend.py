# FC(Function Calling) 기반 챗봇
import os
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from dotenv import load_dotenv
from company_flow_server.rag.vs_manager import VectorStoreManager
from company_flow_server.llm.llm_adapter import get_langchain_llm

# 환경 변수 로드(.env 파일에서 API 키 등을 로드)
load_dotenv()

vs_manager = VectorStoreManager(provider=os.getenv("VS_TYPE", "chroma"))
llm = get_langchain_llm()

class Turn(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: List[Turn]  
    uuid: str

app = FastAPI()

# 기본 프롬프트 구성
base_prompt = """당신은 업무 전문가입니다. \n
운영 현장의 경험이 풍부하고,  운영 상의 이슈/문제를 스마트하고 노련하게 해결합니다. \n
사용자의 질문에 최선을 다해 답변하세요.\n

"""

cs_guide = ''

# Guide prompt content is loaded once at startup and reused for every request.
guide_path = os.path.join(os.path.dirname(__file__), 'docs', 'guide.md')
if not os.path.exists(guide_path):
    guide_path = './docs/guide.md'

try:
    with open(guide_path, 'r', encoding='utf-8') as f:
        cs_guide = f.read()
        print('guide.md loaded successfully.')
except FileNotFoundError:
    cs_guide = ''
    print(f'Warning: {guide_path} not found, continuing without guide prompt.')

system_prompt = base_prompt + '\n\n' + cs_guide
#print("system_prompt :", system_prompt)

# 프롬프트 템플릿 생성
prompt = PromptTemplate.from_template(
    """System: {system_prompt}

You are an AI assistant for customer service. Answer the User Question using ONLY the provided context.
CRITICAL: Do NOT include raw data, JSON, or technical labels like "RAG_Context:" in your output. ONLY provide the final natural conversational response to the user.

<context>
RAG Context (if any):
{retrieved_context}
</context>

Chat History:
{chat_history}

User Question: {question}

Answer:"""
)

# 사용자별 부분 질문 기록
query_histories: Dict[str, List[str]] = {}

# 과거 대화 기록을 저장하기 위한 리스트
chat_histories: Dict[str, List] = {}

def get_final_prompt(query: str, uuid: str) -> str:

    store_id = 'SM1'
    index = store_id + '_chunk'

    #print("query :", query)

    # UUID별 기록을 가져오거나 새로 생성합니다.
    user_query_history = query_histories.setdefault(uuid, [])
    user_chat_history = chat_histories.setdefault(uuid, [])

    # 메제기가 넘어올때마다 저장하여 최근 대화 이력을 유지하는 방식으로, 
    # 고객의 추가 질문이나 보완 질문이 있을 때 이전 맥락을 고려하여 연속성 있는 답변을 제공할 수 있습니다.
    user_query_history.append(query)

    # 최근 3개 질문을 하나의 스트링으로 저장 
    #query_final = ' '.join(user_query_history[-3:])
    query_final = query
    print("\n>>>>> query_final :", query_final)

    try:    
        # 질문에 대한 FAQ 검색
        t0 = time.time()
        chunks = vs_manager.search_chunks(query=query_final, index_name="SM1_chunk", top_k=3)
        print(f"[{time.time()-t0:.2f}s] search_chunks 완료")
        
        if not chunks:
            response = "죄송합니다. 일치하는 FAQ 항목이 없습니다" 
            print(f"response : {response}")
            return None
            
        else :
            context_text = ''
            for chunk in chunks:
                context_text += f'##참조문서_Chunk:\n{chunk}\n\n'
            print("\n>>>>> rag_context:\n", context_text)
            
            # 히스토리 포맷팅 (최근 4개 메시지로 제한)
            history_str = ""
            recent_history = user_chat_history[-4:]
            for msg in recent_history:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                history_str += f"{role}: {msg.content}\n"
                
            rendered = prompt.format(
                system_prompt=system_prompt,
                retrieved_context="[검색된 FAQ Context]\n\n" + context_text,
                question=query,
                chat_history=history_str
            ) 
            user_chat_history.append(HumanMessage(content=query))
            return rendered 

    except Exception as e:
        err = str(e) #.split(" ")[0]
        response = "예기치 않은 에러가 발생했습니다.  잠시 후  다시 시도해 주세요." + '\n' + f'(에러: {err})'
        print(f"response : {response}")
        return None


@app.post("/chat", response_model=Turn)
def chat(messages: Messages) :
    
    query = messages.messages[-1].content
    uuid = messages.uuid

    final_prompt = get_final_prompt(query, uuid)
    if final_prompt is None:
        return {"role": "assistant", "content": "죄송합니다. 질문에 대해서 적정한 답변이 준비되지 않았습니다"}   

    # invoke 방식 (한 번에 전체 응답)
    resp = llm.invoke(final_prompt)
    text = resp.content if hasattr(resp, "content") else str(resp)
    response = text.strip()
    #print("\n>>>>> response :\n", response)

    # 대화 기록에 현재 대화 추가
    chat_histories[uuid].append(AIMessage(content=response))
    #print(f"\n>>>>> Updated chat_history for {uuid}:\n", chat_histories[uuid])

    return {"role": "assistant", "content": response}


@app.post("/chat_stream")
async def chat_stream(messages: Messages):

    query = messages.messages[-1].content
    uuid = messages.uuid

    headers = {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    async def generate():
        start_time = time.time()
        final_prompt = get_final_prompt(query, uuid)
        print(f"[{time.time()-start_time:.2f}s] get_final_prompt 완료")
        if final_prompt is None:
            yield "죄송합니다. 질문에 대해서 적정한 답변이 준비되지 않았습니다"
            return
    
        # stream 방식 (토큰 단위로 스트리밍)
        full_response = ""
        first_token = True
        llm_start = time.time()
        async for chunk in llm.astream(final_prompt):
            if first_token:
                print(f"[{time.time()-llm_start:.2f}s] 첫 토큰 응답 (TTFT)")
                first_token = False
            if chunk.content:
                full_response += chunk.content
                yield chunk.content
        print(f"[{time.time()-llm_start:.2f}s] 전체 스트리밍 완료")

        response = full_response.strip()
        print(f"\n>>>>> Final response :\n", response)

        # 대화 기록에 현재 대화 추가
        chat_histories[uuid].append(AIMessage(content=response))

    return StreamingResponse(generate(), headers=headers)    