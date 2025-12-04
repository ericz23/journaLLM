"""
LLM client using Ollama for local, privacy-preserving inference.
All journal data stays on your machine.
"""

import datetime as dt
import json
import re
from typing import Sequence

import ollama

from backend.core.config import OLLAMA_MODEL
from .context_builder import build_context_window

# System prompt for journal metadata extraction
EXTRACTION_SYSTEM_PROMPT = """You are extracting structured metadata from a personal daily journal entry.

Return ONLY valid JSON. No backticks, no extra text, no explanations.

Use exactly this schema:

{
  "summary": "string, 1-3 sentences summarizing the day",
  "metrics": {
    "mood_score": 5,
    "energy_score": 5,
    "stress_score": 5,
    "sleep_hours": 7.0
  },
  "events": [
    {
      "description": "short description of an event",
      "category": "one of: work, study, social, health, personal, other",
      "effect on mood": 0,
      "people": ["list of people mentioned, if any"]
    }
  ]
}

Rules:
- mood_score, energy_score, stress_score: integers 1-10 (5 is neutral)
- sleep_hours: float (default 7.0 if not mentioned)
- effect on mood: -2 very negative, -1 negative, 0 neutral, 1 positive, 2 very positive
- If something is not mentioned, use neutral defaults

Respond with ONLY the JSON object, nothing else."""

# System prompt for journaling assistant
ASSISTANT_SYSTEM_PROMPT = """You are a personal journaling assistant.
You help the user reflect on their life, goals, emotions, and habits.
For now, you do NOT have direct access to their past journal data.
Just respond thoughtfully based on the user's current message.

Keep answers concise and concrete."""


def _clean_json_response(raw_text: str) -> str:
    """Clean up LLM response to extract valid JSON."""
    raw_text = raw_text.strip()
    
    # Remove markdown code fences if present
    if raw_text.startswith("```"):
        # Remove opening fence (with optional language tag)
        raw_text = re.sub(r"^```(?:json)?\s*\n?", "", raw_text)
        # Remove closing fence
        raw_text = re.sub(r"\n?```\s*$", "", raw_text)
    
    # Find JSON object boundaries
    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1
    if start != -1 and end > start:
        raw_text = raw_text[start:end]
    
    return raw_text.strip()


def _chat(system_prompt: str, user_message: str) -> str:
    """Send a chat message to Ollama and return the response."""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response["message"]["content"].strip()


def extract_journal_metadata(journal_text: str) -> dict:
    """
    Use local Ollama model to extract structured data from a journal entry.
    This keeps sensitive journal data on your local machine.
    Returns a Python dict.
    """
    prompt = f"Here is the daily journal entry text:\n\n{journal_text}"

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    
    raw_text = response["message"]["content"]
    cleaned = _clean_json_response(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse Ollama JSON: {e}\nRaw: {raw_text[:500]}"
        )

    return data


def chat_with_journal_assistant(message: str) -> str:
    """
    Simple chat wrapper: forwards the user's message to Ollama with a journaling-specific system prompt.
    All processing happens locally for privacy.
    """
    return _chat(ASSISTANT_SYSTEM_PROMPT, message)


def chat_with_journal_context(
    message: str,
    start_date: dt.date | str,
    end_date: dt.date | str,
    history: Sequence[tuple[str, str]] | None = None,
) -> str:
    """
    Chat with the assistant using journal context from the specified date window.
    All processing happens locally via Ollama for privacy.
    """
    window_start = _ensure_date(start_date)
    window_end = _ensure_date(end_date)

    context = build_context_window(window_start, window_end)
    context_text = context["text"]

    system_prompt = f"""You are a personal journaling assistant.
You have access to structured journal summaries covering {window_start} to {window_end}.
Use the provided context verbatim; do not fabricate details outside it.
If the context does not mention something, say you are unsure.
Keep answers concise, reflective, and actionable."""

    # Build the user message with context and history
    parts = []
    parts.append("=== Journal Context Start ===")
    parts.append(context_text)
    parts.append("=== Journal Context End ===")
    parts.append("")

    if history:
        parts.append("Conversation history:")
        for idx, (user_msg, assistant_msg) in enumerate(history, start=1):
            parts.append(f"{idx}. User: {user_msg}")
            parts.append(f"{idx}. Assistant: {assistant_msg}")
        parts.append("")

    parts.append(f"User question: {message}")

    user_content = "\n".join(parts)

    return _chat(system_prompt, user_content)


def _ensure_date(value: dt.date | str) -> dt.date:
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(value)
