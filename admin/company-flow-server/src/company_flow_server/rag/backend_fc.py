# FC(Function Calling) 기반 챗봇
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple

from function import *
from llm import get_llm
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from dotenv import load_dotenv
from vs_manager import VectorStoreManager

# 환경 변수 로드(.env 파일에서 API 키 등을 로드)
load_dotenv()

vs_manager = VectorStoreManager(provider=os.getenv("VS_TYPE", "chroma"))
llm = get_llm()

class Turn(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: List[Turn]  
    uuid: str

app = FastAPI()

# 도구 리스트 생성
tools = [
    get_customer_profile,
    search_products,
    get_customer_orders,
    get_delivery_status,
    search_reviews,
    get_customer_cart,
    get_point_history,
    get_current_promotions,
    get_popular_products,
    search_facility
]


# 시스템 프롬프트
SYSTEM_PROMPT_FOR_AGENT = """당신은 이마트 고객 상담사 입니다. 사용자의 질문에 최선을 다해 답변하세요.

1. 고객 프로필, 주문 내역, 배송 상태, 포인트 이력, 프로모션, 장바구니, 상품 리뷰, 인기상품, 시설물(편의시설) 등에 관한 질문은 반드시 도구를 호출하여 답변합니다.
2. 이전 대화 맥락을 참고하여 일관된 답변을 제공합니다.
3. 만약 이전 대화가 없는 최초의 질문인 경우에는  고객 프로필과 최근 주문내역 기반으로 가볍게 인사를 건넵니다. (예, 안녕하세요. OOO님,  최근 구매하신 OOO 은 맘에 드시는 지요?)
4. ID 형식을 정확히 사용하십시오.
5. 현재 로그인한 사용자의 ID는 C001로 가정합니다.
"""


# Fuction Call 처리를 위한 에이전트 생성
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT_FOR_AGENT
)

# 대화 관리 클래스
class ConversationManager:
    def __init__(self):
        self.agent = agent
        self.chat_history = []

    def process_message(self, message: str):
        # 사용자 메시지를 히스토리에 추가
        self.chat_history.append({"role": "user", "content": message})

        # 에이전트 실행
        response = self.agent.invoke({"messages": self.chat_history})

        # 응답에서 마지막 메시지 추출
        last_message = response["messages"][-1]
        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # 어시스턴트 응답을 히스토리에 추가
        self.chat_history.append({"role": "assistant", "content": answer})

        # 실행 로그 생성
        log_content = [f"[User Input] :{message}"]

        # tool_calls 정보 추출
        for msg in response["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    log_content.append(f"[Function Call] : {tool_call['name']}")
                    log_content.append(f"[Parameters] : {tool_call['args']}")
            if hasattr(msg, 'name') and msg.name:  # ToolMessage
                log_content.append(f"[Output] : \n{msg.content}")

        log_content.append(f"[AI Response] : \n{answer}")
        execution_log = "\n".join(log_content)

        return answer, execution_log

    def clear_history(self):
        self.chat_history = []
        return []

# 대화 관리자 인스턴스 생성
conversation_manager = ConversationManager()

#  대화 초기화 함수
def clear_conversation():
    """대화 이력 초기화"""
    conversation_manager.clear_history()
    return [], ""


# AI 상담을 위한 기본 프롬프트 구성
base_prompt = """당신은 이마트 고객만족센터 7년 차 선임 매니저(32세)입니다. \n
현장 경험이 풍부하여 상품권, 결제, 환불 규정에 능통하며, 고객의 문제를 스마트하고 노련하게 해결합니다. \n
사용자의 질문에 최선을 다해 답변하세요.\n
1. 고객 프로필, 주문 내역, 배송 상태, 포인트, 결제 정보 등에 관한 질문은 반드시 도구를 호출하여 답변합니다.\n
2. 해당 도구와 상관없는 질문에 대해서는 RAG_Context 를 기반으로 답변합니다.\n
3. ID 형식을 정확히 사용하십시오.\n
4. 현재 로그인한 사용자의 ID는 C001로 가정합니다. \n\n
"""

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

# 프롬프트 템플릿 생성
prompt = PromptTemplate.from_template(
    """
    Please generate a response to the given Question in accordance with the CS_Guide. 
    If Func_Call_Result exists, prioritize this information for the answer. 
    If it does not exist, generate the response prioritizing RAG_Context. 
    Make sure to refer to the Chat_history to summarize and deliver the final response.

    CS_Guide : {system_prompt}
    Func_Call_Result : {func_call_result}
    RAG_Context : {retrieved_context}
    Question: {question}
    Chat_history: {chat_history}
    """
)

# 사용자별 부분 질문 기록
query_histories: Dict[str, List[str]] = {}

# 과거 대화 기록을 저장하기 위한 리스트
chat_histories: Dict[str, List] = {}

def get_final_prompt(query: str, uuid: str) -> str:

    brand_id = 'EM'
    index = brand_id + '_chunk'

    #print("query :", query)

    # UUID별 기록을 가져오거나 새로 생성합니다.
    user_query_history = query_histories.setdefault(uuid, [])
    user_chat_history = chat_histories.setdefault(uuid, [])

    # 메제기가 넘어올때마다 저장하여 최근 대화 이력을 유지하는 방식으로, 
    # 고객의 추가 질문이나 보완 질문이 있을 때 이전 맥락을 고려하여 연속성 있는 답변을 제공할 수 있습니다.
    user_query_history.append(query)

    # 최근 3개 질문을 하나의 스트링으로 저장 
    query_final = ' '.join(user_query_history[-3:])
    #query_final = query
    print("\n>>>>> query_final :", query_final)

    try:    
        # tool_calls 가 존재하는 경우
        func_call_result, execution_log = conversation_manager.process_message(query)
        print("\n>>>>> function_call_log :\n", execution_log)
        
        # tool_calls 과 상관없이 질문에 대한 FAQ 검색
        chunks = vs_manager.search_chunks(
            query=query_final,
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
            print("\n>>>>> rag_context:\n", context_text)
            rendered = prompt.format(
                system_prompt=system_prompt,
                func_call_result=func_call_result,
                retrieved_context="[검색된 FAQ Context]\n\n" + context_text,
                question=query,
                chat_history=user_chat_history
            ) 
            user_chat_history.append(HumanMessage(content=query))
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
    print("\n>>>>> response :\n", response)

    # 대화 기록에 현재 대화 추가
    chat_histories[uuid].append(AIMessage(content=response))
    print(f"\n>>>>> Updated chat_history for {uuid}:\n", chat_histories[uuid])

    return {"role": "assistant", "content": response}


@app.post("/chat_stream", response_model=Turn)
def chat_stream(messages: Messages) :

    query = messages.messages[-1].content
    uuid = messages.uuid
    #print("query :", query)
    #print("uuid :", uuid)

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
        print("\n>>>>> response :\n", response)

        # 대화 기록에 현재 대화 추가
        chat_histories[uuid].append(AIMessage(content=response))
        print(f"\n>>>>> Updated chat_history for {uuid}:\n", chat_histories[uuid])

    return StreamingResponse(generate(), media_type="text/event-stream")    