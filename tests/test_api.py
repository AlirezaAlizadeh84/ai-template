from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from ai_template.dependencies import get_current_user, get_db
from ai_template.main import app
from ai_template.models import User


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/users/me")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_history_unauthorized():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/chat/history")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_success_with_mock(monkeypatch):
    # ۱. جایگزینی نگهبان کاربر با یک کاربر تستی
    app.dependency_overrides[get_current_user] = lambda: User(
        id=1, email="test@example.com", is_active=True
    )

    # ۲. جایگزینی دیتابیس با یک دیتابیس مشقی
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result
    app.dependency_overrides[get_db] = lambda: mock_db

    # ۳. جایگزینی Ollama با یک تابع فوری تستی
    async def fake_ask_ollama(prompt: str) -> str:
        return "Mocked AI response"

    monkeypatch.setattr(
        "ai_template.routers.chat.ask_ollama", fake_ask_ollama
    )

    # ۴. ارسال درخواست و بررسی نتیجه (کد تو)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/chat", json={"prompt": "Hello"})
        assert response.status_code == 200
        assert response.json()["response"] == "Mocked AI response"

    # ۵. پاک کردن بدلکارها پس از پایان تست
    app.dependency_overrides.clear()