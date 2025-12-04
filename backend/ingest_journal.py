"""
CLI utility to ingest a journal file, extract metadata via local LLM, and persist it.
"""

import argparse
import datetime as dt
import hashlib
import re
from pathlib import Path
from typing import Optional

from backend.db import get_session
from backend.services.llm_client import extract_journal_metadata
from backend.models import Event, JournalEntry, JournalMetadata, Person

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def _parse_date(value: Optional[str]) -> Optional[dt.date]:
    if not value:
        return None
    return dt.date.fromisoformat(value)


def _infer_date_from_filename(path: Path) -> Optional[dt.date]:
    match = DATE_PATTERN.search(path.name)
    if not match:
        return None
    return dt.date.fromisoformat(match.group(0))


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ingest_journal(path: Path, entry_date: dt.date, skip_if_unchanged: bool = True) -> bool:
    """
    Ingest a single file. Returns True if processed (new or updated), False if skipped.
    """
    text = path.read_text(encoding="utf-8")
    file_hash = _content_hash(text)

    with get_session() as session:
        existing = (
            session.query(JournalEntry)
            .filter(JournalEntry.source_path == str(path))
            .one_or_none()
        )

        if existing and skip_if_unchanged and existing.file_hash == file_hash:
            print(f"Skipping unchanged entry: {path}")
            return False

        metadata = extract_journal_metadata(text)

        if existing:
            print(f"Updating existing entry from {path}")
            session.delete(existing)
            session.flush()

        entry = JournalEntry(
            entry_date=entry_date,
            source_path=str(path),
            raw_text=text,
            file_hash=file_hash,
        )
        session.add(entry)
        session.flush()

        metrics = metadata.get("metrics") or {}
        entry_metadata = JournalMetadata(
            entry=entry,
            summary=metadata.get("summary"),
            mood_score=_safe_int(metrics.get("mood_score"), 5),
            energy_score=_safe_int(metrics.get("energy_score"), 5),
            stress_score=_safe_int(metrics.get("stress_score"), 5),
            sleep_hours=_safe_float(metrics.get("sleep_hours"), 7.0),
        )
        session.add(entry_metadata)

        for event_payload in metadata.get("events") or []:
            event = Event(
                entry=entry,
                description=(event_payload.get("description") or "").strip(),
                category=(event_payload.get("category") or "other").strip() or "other",
                effect_on_mood=_safe_int(event_payload.get("effect on mood"), 0),
            )
            people = event_payload.get("people") or []
            for person_name in people:
                if not person_name:
                    continue
                event.people.append(Person(name=person_name.strip()))
            session.add(event)

    print(f"Ingested journal for {entry_date.isoformat()} from {path}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a journal Markdown file.")
    parser.add_argument("path", type=Path, help="Path to the journal Markdown file.")
    parser.add_argument(
        "--date",
        type=str,
        help="Entry date in YYYY-MM-DD. Defaults to date inferred from filename or today.",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Reingest even if the file content has not changed.",
    )
    args = parser.parse_args()

    path: Path = args.path.expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    entry_date = _parse_date(args.date)
    if entry_date is None:
        entry_date = _infer_date_from_filename(path)
    if entry_date is None:
        entry_date = dt.date.today()

    ingest_journal(path, entry_date, skip_if_unchanged=not args.no_skip)


if __name__ == "__main__":
    main()

