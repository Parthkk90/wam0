import ollama
import json
from typing import List, Dict, Any, Optional
from ..infra import RedisCache

COMPACTOR_PROMPT_TEMPLATE = """
You are a financial memory compactor for banking loan officers.

Given these facts from a loan session, produce a consolidated summary:
- Remove contradictions (e.g., income stated as both 55K and 60K)
- Flag verified vs. derived facts
- Output JSON only, no explanation

Facts:
{facts_json}

Output JSON (facts_consolidated, verified_count, derived_count):
"""


class Phi4Compactor:
    def __init__(self, ollama_api: str = "http://localhost:11434"):
        self.ollama_api = ollama_api

    async def compact(
        self,
        facts: List[Dict],
        redis_cache: Optional[RedisCache] = None,
        bank_id: str = "",
        customer_id: str = "",
    ) -> Dict[str, Any]:
        """Compactor prompt to Phi-4-Mini"""
        prompt = COMPACTOR_PROMPT_TEMPLATE.format(
            facts_json=json.dumps(facts, indent=2)
        )

        response = ollama.chat(
            model='phi4-mini',
            base_url=self.ollama_api,
            messages=[{'role': 'user', 'content': prompt}],
            stream=False
        )

        summary_text = response['message']['content']
        try:
            summary_json = json.loads(summary_text)
        except json.JSONDecodeError:
            # Phi-4-Mini might not output pure JSON
            summary_json = {"raw": summary_text, "parsed": False}

        # Write summary to Redis cache if available
        if redis_cache is not None and customer_id:
            summary_json_str = json.dumps(summary_json)
            await redis_cache.set_summary(customer_id, summary_json_str)

        return summary_json
