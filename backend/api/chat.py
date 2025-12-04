"""
Chat API endpoints for the journal assistant.
"""

from datetime import date
from typing import List, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.llm_client import chat_with_journal_context

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    start_date: date
    end_date: date


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the journal assistant with context from the specified date range.
    """
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be on or before end date"
        )

    # Convert history to the format expected by the LLM client
    history_tuples: List[Tuple[str, str]] = []
    for i in range(0, len(request.history) - 1, 2):
        if (request.history[i].role == "user" and 
            i + 1 < len(request.history) and 
            request.history[i + 1].role == "assistant"):
            history_tuples.append((
                request.history[i].content,
                request.history[i + 1].content
            ))

    try:
        response = chat_with_journal_context(
            message=request.message,
            start_date=request.start_date,
            end_date=request.end_date,
            history=history_tuples if history_tuples else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from assistant: {str(e)}"
        )

    return ChatResponse(
        response=response,
        start_date=request.start_date,
        end_date=request.end_date,
    )

