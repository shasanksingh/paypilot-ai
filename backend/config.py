import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "paypilot.db"

USE_REMOTE_LLM = os.getenv("USE_REMOTE_LLM", "").lower() in {"1", "true", "yes"}

BASE_URL = os.getenv("GENAI_BASE_URL", "https://genailab.tcs.in")
API_KEY = os.getenv("GENAI_API_KEY", "")

MAIN_MODEL = os.getenv("PAYPILOT_MAIN_MODEL", "genailab-maas-gpt-5.4")
FAST_MODEL = os.getenv("PAYPILOT_FAST_MODEL", "azure/genailab-maas-gpt-4o-mini")

requested_reasoning_model = os.getenv("PAYPILOT_REASONING_MODEL", FAST_MODEL)
REASONING_MODEL = (
    FAST_MODEL
    if requested_reasoning_model == "azure_ai/genailab-maas-DeepSeek-R1"
    else requested_reasoning_model
)
CODE_MODEL = os.getenv("PAYPILOT_CODE_MODEL", "genailab-maas-gpt-5.3-codex")
EMBEDDING_MODEL = os.getenv("PAYPILOT_EMBEDDING_MODEL", "azure/genailab-maas-text-embedding-3-large")

MAX_RETRIES = 3
CONFIDENCE_THRESHOLD = 80

APP_CONFIG = {
    "MINIMUM_SAFE_BALANCE": 10000,
    "APPROVAL_REQUIRED_ABOVE": 5000,
    "HIGH_RISK_THRESHOLD": 70,
    "MEDIUM_RISK_THRESHOLD": 40,
    "AUTOPAY_LIMIT": 2000
}
