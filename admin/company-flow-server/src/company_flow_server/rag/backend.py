from typing import List
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
from typing import Dict, List, Optional, Tuple
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from vs_manager import VectorStoreManager
from company_flow_server.llm.llm_adapter import get_langchain_llm

from dotenv import load_dotenv
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
base_prompt = "당신은 이마트 고객만족센터 7년 차 선임 매니저(32세)입니다. \n현장 경험이 풍부하여 상품권, 결제, 환불 규정에 능통하며, 고객의 문제를 스마트하고 노련하게 해결합니다."
cs_guide = ''

# Guide prompt content is loaded once at startup and reused for every request.
try:
    with open('./docs/guide.md', 'r', encoding='utf-8') as f:
        cs_guide = f.read()
        print('guide.md loaded successfully.')
except FileNotFoundError:
    cs_guide = ''
    print('Warning: docs/guide.md not found, continuing without guide prompt.')

system_prompt = base_prompt + '\n\n' + cs_guide
#print("system_prompt :", system_prompt)

# 1. 프롬프트 템플릿 생성
prompt = PromptTemplate.from_template(
    """
    Answer the Question based on the CS_Guide, retrieved RAG_Context, and Chat_history.

    CS_Guide : {system_prompt}
    Chat_history: {chat_history}
    RAG_Context : {retrieved_context}
    Question: {question}
    """
)

# 사용자별 부분 질문 기록
query_histories: Dict[str, List[str]] = {}

# 과거 대화 기록을 저장하기 위한 리스트
chat_histories: Dict[str, List] = {}

def get_final_prompt(query: str, uuid: str) -> str:

    brand_id = 'EM'
    index = brand_id + '_chunk'

    print("query :", query)

    # UUID별 기록을 가져오거나 새로 생성합니다.
    user_query_history = query_histories.setdefault(uuid, [])
    user_chat_history = chat_histories.setdefault(uuid, [])

    # 메제기가 넘어올때마다 저장하여 최근 대화 이력을 유지하는 방식으로, 
    # 고객의 추가 질문이나 보완 질문이 있을 때 이전 맥락을 고려하여 연속성 있는 답변을 제공할 수 있습니다.
    user_query_history.append(query)

    # 최근 3개 질문을 하나의 스트링으로 저장 
    query_final = ' '.join(user_query_history[-3:])
    print("query_final :", query_final)

    try:    
        chunks = vs_manager.search_chunks(
            query=query.lower(),
            index_name=index,
            top_k=3
        )
        
        #print("chunks :", chunks)
        if not chunks:
            response = "죄송합니다. 일치하는 FAQ 항목이 없습니다" 
            print(f"response : {response}")
            return None
            
        else :
            context_text = ''
            for chunk in chunks:
                context_text += f'##참조문서_Chunk:\n{chunk}\n\n'
            #print("context_text :", context_text)
            rendered = prompt.format(
                system_prompt=system_prompt,
                retrieved_context="[검색된 FAQ Context]\n\n" + context_text,
                question=query_final,
                chat_history=user_chat_history
            ) 
            user_chat_history.append(HumanMessage(content=query_final))
            #chat_histories[uuid].append(HumanMessage(content=query_final))
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
    print("response :", response)

    # 대화 기록에 현재 대화 추가
    chat_histories[uuid].append(AIMessage(content=response))
    print(f"Updated chat_history for {uuid}:", chat_histories[uuid])

    return {"role": "assistant", "content": response}


@app.post("/chat_stream", response_model=Turn)
def chat_stream(messages: Messages) :

    query = messages.messages[-1].content
    uuid = messages.uuid
    print("query :", query)
    print("uuid :", uuid)

    def generate():

        final_prompt = get_final_prompt(query, uuid)
        if final_prompt is None:
            yield "죄송합니다. 질문에 대해서 적정한 답변이 준비되지 않았습니다"
            return
    
        # stream 방식 (토큰 단위로 스트리밍)
        full_response = ""
        for chunk in llm.stream(final_prompt):
            full_response += chunk.content
            yield chunk.content

        response = full_response.strip()
        print("response :", response)

        # 대화 기록에 현재 대화 추가
        chat_histories[uuid].append(AIMessage(content=response))
        print(f"Updated chat_history for {uuid}:", chat_histories[uuid])

    return StreamingResponse(generate(), media_type="text/event-stream")