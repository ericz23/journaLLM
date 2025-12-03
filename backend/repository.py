"""
Lightweight data access helpers for journal storage.
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from .db import get_session
from .models import Event, JournalEntry, JournalMetadata, Person


def _serialize_entry(entry: JournalEntry) -> Dict:
    meta: Optional[JournalMetadata] = entry.entry_metadata
    return {
        "id": entry.id,
        "date": entry.entry_date,
        "summary": meta.summary if meta else None,
        "metrics": {
            "mood_score": meta.mood_score if meta else None,
            "energy_score": meta.energy_score if meta else None,
            "stress_score": meta.stress_score if meta else None,
            "sleep_hours": meta.sleep_hours if meta else None,
        },
        "events": [
            {
                "id": evt.id,
                "description": evt.description,
                "category": evt.category,
                "effect_on_mood": evt.effect_on_mood,
                "people": [person.name for person in evt.people],
            }
            for evt in entry.events
        ],
        "source_path": entry.source_path,
    }


def list_entries_between(start: dt.date, end: dt.date) -> List[Dict]:
    """
    Return serialized entries between the two dates inclusive.
    """
    with get_session() as session:
        query = (
            select(JournalEntry)
            .options(
                joinedload(JournalEntry.entry_metadata),
                joinedload(JournalEntry.events).joinedload(Event.people),
            )
            .where(JournalEntry.entry_date.between(start, end))
            .order_by(JournalEntry.entry_date.asc())
        )
        rows = session.execute(query).unique().scalars().all()
        return [_serialize_entry(row) for row in rows]


def list_recent_entries(days: int = 14) -> List[Dict]:
    """
    Convenience helper to fetch the most recent entries.
    """
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    return list_entries_between(start, end)
