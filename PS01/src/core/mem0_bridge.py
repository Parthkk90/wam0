# src/core/mem0_bridge.py
import json
import logging
from typing import List, Dict, Optional
from mem0 import Memory
from .wal import WALLogger
from ..api.middleware import require_consent
from ..infra import RedisCache

logger = logging.getLogger(__name__)


class Mem0Bridge:
    def __init__(self, memory: Memory, wal_logger: WALLogger, bank_id: str = "default", redis_cache: Optional[RedisCache] = None):
        self.memory = memory
        self.wal = wal_logger
        self.bank_id = bank_id
        self.redis_cache = redis_cache

    @require_consent(scope="home_loan_processing")
    async def add_with_wal(self, session_id: str, customer_id: str, agent_id: str, facts: List[Dict], bank_id: str = ""):
        """
        Step 1: Write WAL
        Step 2: Acquire Redis lock (non-blocking)
        Step 3: Write Mem0
        Step 4: Release Redis lock
        Step 5: Return status
        """
        effective_bank_id = bank_id or self.bank_id
        composite_user_id = f"{effective_bank_id}::{customer_id}"

        try:
            # Step 1: WAL append (crash-safe)
            self.wal.append(session_id, customer_id, agent_id, effective_bank_id, facts)

            # Step 2: Acquire Redis lock (non-blocking for hackathon)
            lock_token = None
            if self.redis_cache is not None:
                lock_token = await self.redis_cache.acquire_lock(customer_id)
                if lock_token is None:
                    logger.warning("Could not acquire Redis lock for customer=%s; proceeding without lock", customer_id)

            # Step 3: mem0.add()
            try:
                self.memory.add(
                    messages=[{
                        "role": "system",
                        "content": json.dumps(facts)
                    }],
                    user_id=composite_user_id,
                    agent_id=agent_id
                )
            finally:
                # Step 4: Release lock if acquired
                if self.redis_cache is not None and lock_token is not None:
                    await self.redis_cache.release_lock(customer_id, lock_token)

            return {"status": "ok", "facts_added": len(facts)}
        except Exception as e:
            # WAL survives crash; Mem0 write failed but can retry
            return {"status": "error", "wal_written": True, "error": str(e)}
