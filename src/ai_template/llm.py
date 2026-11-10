import json
from collections.abc import AsyncGenerator
import httpx
from ai_template.config import settings





async def ask_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()

    data = response.json()
    return data["response"]




async def stream_ollama(prompt: str) -> AsyncGenerator[str, None]:
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_base_url}/api/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line).get("response", "")
                    yield chunk

                    