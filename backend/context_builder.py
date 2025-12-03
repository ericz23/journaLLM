"""
Helpers to assemble journal context snippets for the assistant.
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from .repository import list_entries_between, list_recent_entries


def _avg(values: List[Optional[float]]) -> Optional[float]:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def _format_metric_line(metrics: Dict[str, Optional[float]]) -> str:
    parts = []
    for key in ("mood_score", "energy_score", "stress_score", "sleep_hours"):
        value = metrics.get(key)
        if value is not None:
            parts.append(f"{key.replace('_', ' ').title()}: {value}")
    return " | ".join(parts) if parts else "No metrics available."


def _build_context_payload(entries: List[Dict], coverage_line: str) -> Dict:
    metrics = {
        "mood_score": _avg([e["metrics"]["mood_score"] for e in entries if e.get("metrics")]),
        "energy_score": _avg([e["metrics"]["energy_score"] for e in entries if e.get("metrics")]),
        "stress_score": _avg([e["metrics"]["stress_score"] for e in entries if e.get("metrics")]),
        "sleep_hours": _avg([e["metrics"]["sleep_hours"] for e in entries if e.get("metrics")]),
    }

    lines: List[str] = []
    lines.append(coverage_line)
    lines.append("Averages → " + _format_metric_line(metrics))

    for entry in entries:
        date_value = entry["date"]
        date_str = date_value.strftime("%Y-%m-%d") if isinstance(date_value, dt.date) else str(date_value)
        summary = entry.get("summary") or "(no summary)"
        events = entry.get("events") or []
        top_event = events[0] if events else None
        if top_event:
            event_text = f"Key event: {top_event['description']}"
            if top_event.get("people"):
                event_text += f" (people: {', '.join(top_event['people'])})"
        else:
            event_text = "No events captured."
        lines.append(f"- {date_str}: {summary} | {event_text}")

    return {
        "entries": entries,
        "metrics": metrics,
        "text": "\n".join(lines),
    }


def build_recent_context(days: int = 14) -> Dict:
    """
    Fetch recent entries and return both structured data and formatted text snippets.
    """
    entries = list_recent_entries(days=days)
    if entries:
        coverage_line = (
            f"Recent journal coverage: {entries[0]['date']} to {entries[-1]['date']} "
            f"({len(entries)} entries)."
        )
    else:
        coverage_line = "No journal entries stored yet."
    return _build_context_payload(entries, coverage_line)


def build_context_window(
    start: dt.date,
    end: dt.date,
) -> Dict:
    """
    Build a context package for entries within an explicit date window.
    """
    entries = list_entries_between(start, end)

    if entries:
        coverage_line = (
            f"Context window coverage: {entries[0]['date']} to {entries[-1]['date']} "
            f"({len(entries)} entries)."
        )
    else:
        coverage_line = f"No journal entries stored between {start} and {end}."

    return _build_context_payload(entries, coverage_line)

