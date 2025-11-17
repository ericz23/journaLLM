import json
import google.generativeai as genai
from .config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

def get_model():
    return genai.GenerativeModel(MODEL_NAME)


def extract_journal_metadata(journal_text: str) -> dict:
    """
    Call Gemini to extract structured data from a single daily journal entry.
    Returns a Python dict.
    """
    model = get_model()

    system_instructions = """
You are extracting structured metadata from a personal daily journal entry.

Return ONLY valid JSON. No backticks, no extra text.

Use exactly this schema:

{
  "summary": "string, 1-3 sentences summarizing the day",
  "metrics": {
    "mood_score": int,          // 1-10, best guess based on text
    "energy_score": int,        // 1-10
    "stress_score": int,        // 1-10
    "sleep_hours": float,       // hours of sleep last night
  },
  "events": [
    {
      "description": "short description of an event",
      "category": "one of: work, study, social, health, personal, other",
      "effect on mood": int,         // -2 very negative, -1 negative, 0 neutral, 1 positive, 2 very positive
      "people": [ "list of people mentioned, if any" ]
    }
  ]
}

If something is not mentioned, make a reasonable guess or set a neutral default:
- mood/energy/stress default to 5 if unclear
- sleep_hours default to 7.0
"""

    prompt = (
        system_instructions
        + "\n\nHere is the daily journal entry text:\n\n"
        + journal_text
        + "\n\nRemember: respond with ONLY RAW JSON. DO NOT warp output with code fences ever"
    )

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Basic cleanup if model wraps with code fences
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        # sometimes "json\n{...}"
        if raw_text.lstrip().startswith("json"):
            raw_text = raw_text.split("\n", 1)[1]

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Gemini JSON: {e}\nRaw: {raw_text[:500]}")

    return data


def chat_with_journal_assistant(message: str) -> str:
    """
    Simple chat wrapper: forwards the user's message to Gemini with a journaling-specific system prompt.
    """
    model = get_model()

    system_instructions = """
You are a personal journaling assistant.
You help the user reflect on their life, goals, emotions, and habits.
For now, you do NOT have direct access to their past journal data.
Just respond thoughtfully based on the user's current message.

Keep answers concise and concrete.
"""

    prompt = system_instructions + "\n\nUser: " + message + "\nAssistant:"

    response = model.generate_content(prompt)
    return response.text.strip()