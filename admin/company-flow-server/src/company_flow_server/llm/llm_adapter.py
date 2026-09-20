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