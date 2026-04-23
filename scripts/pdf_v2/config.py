"""PDF V2 Pipeline - Configuration Module"""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent

DATA_DIR = BASE_DIR / os.getenv("DATA_PATH", "data")
DB_DIR = BASE_DIR / os.getenv("DB_PATH", "db/chroma")
OUTPUT_DIR = BASE_DIR / "dist" / "pdf"

DATA_PATH = DATA_DIR / "resume.yaml"
DB_PATH = DB_DIR
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "dist/pdf/tailored_resume.pdf")
TEMPLATE_PATH = BASE_DIR / os.getenv("TEMPLATE_PATH", "templates/latex/resume_tailored.tex")

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 1536))

MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 5))
MAX_BULLETS = int(os.getenv("MAX_BULLETS", 12))
MAX_BULLET_CHARS = int(os.getenv("MAX_BULLET_CHARS", 150))

LATEX_COMPILER = os.getenv("LATEX_COMPILER", "xelatex")

def get_llm_client():
    """Get litellm-compatible client."""
    import httpx
    return httpx.Client(
        base_url=LLM_BASE_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        timeout=60.0
    )

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for texts using litellm-compatible API."""
    import httpx
    
    response = httpx.Client(
        base_url=LLM_BASE_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        timeout=30.0
    ).post("/embeddings", json={
        "model": EMBEDDING_MODEL,
        "input": texts
    })
    
    if response.status_code != 200:
        raise Exception(f"Embedding failed: {response.text}")
    
    data = response.json()
    return [item["embedding"] for item in data["data"]]