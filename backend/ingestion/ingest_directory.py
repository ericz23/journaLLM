"""
Batch ingest all Markdown notes within a directory.
"""

import argparse
import datetime as dt
from pathlib import Path
from typing import Optional

from backend.ingestion.ingest_journal import ingest_journal, _infer_date_from_filename


def ingest_directory(notes_dir: Path, skip_if_unchanged: bool = True) -> None:
    paths = sorted(
        [p for p in notes_dir.glob("**/*.md") if p.is_file()],
        key=lambda p: p.name,
    )

    if not paths:
        print(f"No Markdown files found under {notes_dir}")
        return

    processed = 0
    skipped = 0
    errors = 0

    for path in paths:
        entry_date: Optional[dt.date] = _infer_date_from_filename(path)
        if entry_date is None:
            print(f"Skipping {path} (no date in filename).")
            skipped += 1
            continue
        try:
            did_ingest = ingest_journal(path, entry_date, skip_if_unchanged=skip_if_unchanged)
            if did_ingest:
                processed += 1
            else:
                skipped += 1
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Failed ingest for {path}: {exc}")
            errors += 1

    print(
        f"Batch ingest complete. Processed: {processed}, skipped: {skipped}, errors: {errors}."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch ingest all Markdown notes.")
    parser.add_argument(
        "--notes-dir",
        type=Path,
        default=Path("notes"),
        help="Directory containing Markdown notes (default: ./notes).",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Reingest even if files appear unchanged.",
    )
    args = parser.parse_args()

    notes_dir = args.notes_dir.expanduser().resolve()
    if not notes_dir.exists():
        raise SystemExit(f"Notes directory not found: {notes_dir}")

    ingest_directory(notes_dir, skip_if_unchanged=not args.no_skip)


if __name__ == "__main__":
    main()


