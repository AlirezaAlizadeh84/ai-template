from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import httpx
from sqlalchemy import delete, select

from ai_template.config import settings
from ai_template.database import AsyncSessionLocal
from ai_template.dependencies import CurrentUserDep, DBDep
from ai_template.llm import ask_ollama, stream_ollama
from ai_template.models import ChatMessage
from ai_template.schemas import ChatHistoryResponse, ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: CurrentUserDep, db: DBDep):
    query = (
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(5)
    )
    result = await db.execute(query)
    recent_messages = result.scalars().all()

    if recent_messages:
        context = ""
        for msg in reversed(recent_messages):
            context += f"User: {msg.prompt}\nAI: {msg.response}\n"
        full_prompt = (
            f"Previous conversation:\n{context}\nCurrent question:\nUser: {request.prompt}"
        )
    else:
        full_prompt = request.prompt

    try:
        ai_reply = await ask_ollama(full_prompt)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service is currently unavailable: {str(e)}",
        )

    chat_message = ChatMessage(
        user_id=current_user.id,
        prompt=request.prompt,
        response=ai_reply,
        model=settings.ollama_model,
    )
    db.add(chat_message)
    await db.commit()

    return ChatResponse(response=ai_reply, model=settings.ollama_model)


@router.get("/history", response_model=list[ChatHistoryResponse])
async def get_chat_history(
    db: DBDep,
    current_user: CurrentUserDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    query = (
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_history(current_user: CurrentUserDep, db: DBDep):
    query = delete(ChatMessage).where(ChatMessage.user_id == current_user.id)
    await db.execute(query)
    await db.commit()


@router.post("/stream")
async def chat_stream(
    request: ChatRequest, current_user: CurrentUserDep, db: DBDep
):
    query = (
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(5)
    )
    result = await db.execute(query)
    recent_messages = result.scalars().all()

    if recent_messages:
        context = ""
        for msg in reversed(recent_messages):
            context += f"User: {msg.prompt}\nAI: {msg.response}\n"

        full_prompt = (
            f"Previous conversation:\n{context}\nCurrent question:\nUser: {request.prompt}"
        )
    else:
        full_prompt = request.prompt

    async def response_generator():
        full_response = ""
        try:
            async for chunk in stream_ollama(full_prompt):
                full_response += chunk
                yield chunk
        except httpx.HTTPError as e:
            yield f"\n[Error: AI service unavailable - {str(e)}]"
            return

        async with AsyncSessionLocal() as session:
            chat_message = ChatMessage(
                user_id=current_user.id,
                prompt=request.prompt,
                response=full_response,
                model=settings.ollama_model,
            )
            session.add(chat_message)
            await session.commit()

    return StreamingResponse(response_generator(), media_type="text/plain")


@router.delete("/history/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_single_message(
    message_id: int, current_user: CurrentUserDep, db: DBDep
):
    query = select(ChatMessage).where(
        ChatMessage.id == message_id,
        ChatMessage.user_id == current_user.id,
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or does not belong to this user",
        )

    await db.delete(record)
    await db.commit()
    