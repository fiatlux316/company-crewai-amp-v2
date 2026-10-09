import os
from typing import Any
from crewai.llms.base_llm import BaseLLM
from crewai.llms.providers.bedrock.completion import BedrockCompletion
from crewai.llms.providers.gemini.completion import GeminiCompletion
from company_flow_server.llm.devx_llm_wrapper import CompanyLLMWrapper
from company_flow_server.llm.base import CompanyBaseLLM


class DynamicLLMAdapter(CompanyBaseLLM):
    """
    옵션(LLM_TYPE)에 따라 런타임에서 CompanyLLMWrapper, BedrockCompletion, GeminiCompletion 중
    적합한 LLM 인스턴스를 동적으로 생성하고 call을 위임하는 어댑터.
    기존 OpenAICompatibleCompanyLLM을 대체하여 동작합니다.
    """
    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 30.0,
        temperature: float | None = 0.0,
    ) -> None:
        super().__init__(model=model, temperature=temperature)
        llm_type = os.getenv("LLM_TYPE", "company-llm-gateway")

        if llm_type == "company-llm-gateway":
            devx_model = os.getenv("DEVX_MODEL") or model or "bedrock/global.anthropic.claude-sonnet-5"
            print(f"사내 생성형 AI API 호출 : {devx_model}")
            self._inner_llm = CompanyLLMWrapper(
                model=devx_model,
                base_url=os.getenv("DEVX_API_URL") or base_url,
                api_key=os.getenv("DEVX_API_KEY") or api_key,
                timeout_seconds=timeout_seconds,
                temperature=temperature
            )
        elif llm_type == "aws-bedrock":
            bedrock_model = os.getenv("BEDROCK_MODEL") or model
            print(f"AWS Bedrock 호출 : {bedrock_model}")
            self._inner_llm = BedrockCompletion(
                model=bedrock_model,
                region_name=os.getenv("BEDROCK_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            )
        elif llm_type == "gemini":
            gemini_model = os.getenv("GEMINI_MODEL") or model
            print(f"Gemini 호출 : {gemini_model}")
            self._inner_llm = GeminiCompletion(
                model=gemini_model,
                api_key=os.getenv("GEMINI_API_KEY", ""),
            )
        elif llm_type == "ollama":
            ollama_model = os.getenv("OLLAMA_MODEL") or model or "gemma2"
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1/chat/completions")
            print(f"Ollama 호출 : {ollama_model}")
            self._inner_llm = CompanyLLMWrapper(
                model=ollama_model,
                base_url=ollama_base_url,
                api_key="ollama",
                timeout_seconds=timeout_seconds,
                temperature=temperature
            )
        else:
            raise ValueError(f"지원하지 않는 LLM_TYPE 입니다: {llm_type}")

    def call(self, messages: Any, **kwargs: Any) -> Any:
        # GeminiCompletion 등 일부 제공자는 call() 시점의 temperature kwarg를 지원하지 않을 수 있으므로 제거합니다.
        if isinstance(self._inner_llm, (GeminiCompletion, BedrockCompletion)):
            kwargs.pop("temperature", None)
            
        try:
            return self._inner_llm.call(messages, **kwargs)
        except TypeError as e:
            # 예상치 못한 다른 kwarg가 있을 경우를 대비해 덜 엄격하게 처리할 수 있습니다.
            if "unexpected keyword argument" in str(e):
                import re
                match = re.search(r"unexpected keyword argument '([^']+)'", str(e))
                if match:
                    bad_kwarg = match.group(1)
                    kwargs.pop(bad_kwarg, None)
                    return self._inner_llm.call(messages, **kwargs)
            raise e

    def supports_function_calling(self) -> bool:
        if hasattr(self._inner_llm, "supports_function_calling"):
            return self._inner_llm.supports_function_calling()
        return True

    def supports_stop_words(self) -> bool:
        if hasattr(self._inner_llm, "supports_stop_words"):
            return self._inner_llm.supports_stop_words()
        return True

def get_langchain_llm():
    """LangChain 기반으로 동작하는 컴포넌트(예: RAG 챗봇)를 위한 LLM 팩토리 함수"""
    from langchain.chat_models import init_chat_model
    from langchain_openai import ChatOpenAI
    
    llm_type = os.getenv("LLM_TYPE", "company-llm-gateway")
    
    if llm_type == "company-llm-gateway":
        devx_model = os.getenv("DEVX_MODEL", "bedrock/global.anthropic.claude-sonnet-5")
        print(f"사내 생성형 AI API 호출 : {devx_model}")
        devx_url = os.getenv("DEVX_API_URL", "")
        base_url = os.getenv("COMPANY_LLM_BASE_URL") or (devx_url.replace("/chat/completions", "") if devx_url else None)
        return ChatOpenAI(
            model=devx_model,
            base_url=base_url,
            api_key=os.getenv("DEVX_API_KEY") or os.getenv("COMPANY_LLM_API_KEY"),
            temperature=float(os.getenv("DEVX_TEMPERATURE", "0.0")),
            max_tokens=8000
        )
    elif llm_type == "aws-bedrock":
        bedrock_model = os.getenv("BEDROCK_MODEL")
        top_k_env = os.getenv("BEDROCK_TOP_K", "5")
        return init_chat_model(
            model=f"bedrock:{bedrock_model}",
            region_name=os.getenv('BEDROCK_REGION', 'us-east-1'),
            temperature=0.0,
            max_tokens=8000,
            model_kwargs={"top_k": int(top_k_env)}
        )
        
    elif llm_type == "gemini":
        gemini_model = os.getenv("GEMINI_MODEL")
        print(f"Gemini 호출 : {gemini_model}")
        return init_chat_model(
            model=f"google_genai:{gemini_model}",
            api_key=os.getenv('GEMINI_API_KEY'),
            temperature=0.0
        )
    elif llm_type == "ollama":
        from langchain_ollama import ChatOllama
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma2")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        print(f"Ollama 호출 : {ollama_model}")
        return ChatOllama(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.0
        )
    else:
        raise ValueError(f"지원하지 않는 LLM_TYPE 입니다: {llm_type}")
