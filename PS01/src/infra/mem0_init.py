from mem0 import Memory
from pathlib import Path
import os


def init_mem0(bank_id: str = "default") -> Memory:
    vector_db_base = os.getenv("MEM0_VECTOR_DB_PATH", "./chroma_db")
    history_db_base = os.getenv("MEM0_HISTORY_DB_PATH", "./mem0_history")
    ollama_api = os.getenv("OLLAMA_API", "http://localhost:11434")

    vector_db_path = os.path.join(vector_db_base, bank_id)
    history_db_path = os.path.join(history_db_base, bank_id)

    Path(vector_db_path).mkdir(parents=True, exist_ok=True)
    Path(history_db_path).mkdir(parents=True, exist_ok=True)

    memory = Memory.from_config({
        "llm": {
            "provider": "ollama",
            "model": "phi4-mini",
            "base_url": ollama_api
        },
        "embedder": {
            "provider": "ollama",
            "model": "nomic-embed-text"
        },
        "vector_store": {
            "provider": "chromadb",
            "path": vector_db_path
        },
        "history_db_path": history_db_path
    })
    return memory
