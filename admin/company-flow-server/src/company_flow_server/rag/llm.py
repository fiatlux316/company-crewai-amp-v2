
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
load_dotenv()

llm = None

def get_llm():
    
    global llm
    if llm is None:
        if os.getenv("LLM_MODEL") == "gemini":
            llm = init_chat_model(
                model=f"google_genai:{os.getenv('GEMINI_MODEL')}",
                api_key=os.getenv('GEMINI_API_KEY'),
            )
        elif os.getenv("LLM_MODEL") == "claude":
            top_k_env = os.getenv("BEDROCK_TOP_K", "5")
            model_kwargs = {}
            model_kwargs["top_k"] = int(top_k_env)
            llm = init_chat_model(
                model=f"bedrock:{os.getenv('BEDROCK_MODEL')}",
                region_name=os.getenv('BEDROCK_REGION', 'ap-southeast-2'),
                temperature=0.0,
                max_tokens=8000,
                model_kwargs=model_kwargs
            )
        elif os.getenv("LLM_MODEL") == "chatgpt":
            llm = init_chat_model(
                model=f"openai:{os.getenv('CHATGPT_MODEL', 'gpt-4.1')}",
                api_key=os.getenv('OPENAI_API_KEY'),
            )
        else:    
            raise ValueError(f"지원하지 않는 LLM 모델입니다: {os.getenv('LLM_MODEL')}")

    return llm