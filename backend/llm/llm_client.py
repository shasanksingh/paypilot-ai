import json
import httpx

from config import (
    USE_REMOTE_LLM,
    BASE_URL,
    API_KEY,
    MAIN_MODEL,
    FAST_MODEL,
    REASONING_MODEL,
    EMBEDDING_MODEL,
)

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except Exception:
    ChatOpenAI = None
    OpenAIEmbeddings = None


def log_step(message: str) -> None:
    print(message, flush=True)


disabled_model_types = set()


http_client = (
    httpx.Client(verify=False, timeout=httpx.Timeout(8.0))
    if USE_REMOTE_LLM and API_KEY and httpx is not None
    else None
)


if USE_REMOTE_LLM and API_KEY and OpenAIEmbeddings and http_client:
    embeddings = OpenAIEmbeddings(
        base_url=BASE_URL,
        model=EMBEDDING_MODEL,
        api_key=API_KEY,
        http_client=http_client,
    )
else:
    embeddings = None
    log_step("[local] Remote embeddings disabled; RAG memory will use keyword fallback")


def model_supports_custom_temperature(model_name: str) -> bool:
    normalized = (model_name or "").lower()
    return "gpt-5" not in normalized


def get_temperature_for_model(model_name: str):
    if model_supports_custom_temperature(model_name):
        return 0.2

    return 1


def is_missing_deployment_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "deploymentnotfound" in text or "deployment for this resource does not exist" in text


def is_unsupported_temperature_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "unsupportedparamserror" in text and "temperature" in text


def build_llm(model_name: str):
    if USE_REMOTE_LLM and API_KEY and ChatOpenAI and http_client:
        return ChatOpenAI(
            base_url=BASE_URL,
            model=model_name,
            api_key=API_KEY,
            http_client=http_client,
            temperature=get_temperature_for_model(model_name),
            request_timeout=8,
            max_retries=0,
        )

    log_step(f"[local] Remote LLM disabled for model {model_name}; using rule-based fallback")
    return None


main_llm = build_llm(MAIN_MODEL)
fast_llm = build_llm(FAST_MODEL)
reasoning_llm = build_llm(REASONING_MODEL)


llm_registry = {
    "main": main_llm,
    "fast": fast_llm,
    "reasoning": reasoning_llm,
}

model_name_registry = {
    "main": MAIN_MODEL,
    "fast": FAST_MODEL,
    "reasoning": REASONING_MODEL,
}


def get_llm(model_type: str):
    if model_type in disabled_model_types:
        return None

    return llm_registry.get(model_type) or main_llm


def disable_remote_model(model_type: str, exc: Exception) -> None:
    disabled_model_types.add(model_type)
    model_name = model_name_registry.get(model_type, model_type)

    if is_missing_deployment_error(exc):
        reason = "deployment is unavailable"
    elif is_unsupported_temperature_error(exc):
        reason = "model rejected request parameters"
    else:
        reason = "remote call failed"

    log_step(
        f"[llm-fallback] {model_type} model '{model_name}' disabled for this process: "
        f"{reason}. Using deterministic fallback."
    )


def safe_json_loads(text: str, fallback: dict):
    try:
        if not text:
            return fallback

        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        return json.loads(cleaned)
    except Exception:
        return fallback


def call_llm_json(prompt: str, fallback: dict, model_type: str = "main") -> dict:
    """
    Calls remote LLM and expects JSON response.
    If LLM is disabled or fails, returns fallback.
    """

    llm = get_llm(model_type)

    if llm is None:
        return fallback

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return safe_json_loads(content, fallback)
    except Exception as exc:
        disable_remote_model(model_type, exc)
        return fallback


def call_llm_text(prompt: str, fallback: str, model_type: str = "main") -> str:
    """
    Calls remote LLM and expects text response.
    If LLM is disabled or fails, returns fallback.
    """

    llm = get_llm(model_type)

    if llm is None:
        return fallback

    try:
        response = llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        disable_remote_model(model_type, exc)
        return fallback
