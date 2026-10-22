import httpx
from ai_template.config import settings

async def ask_ollama(prompt:str) -> str :
    async with httpx.AsyncClient(timeout = 60.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json = {
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False

            }
        )
        response.raise_for_status()    

    data = response.json()
    return data["response"]



