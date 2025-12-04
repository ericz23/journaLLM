"""
Simple CLI to chat with the journal assistant using a date-window context.
"""

import argparse
import datetime as dt

from backend.services.gemini_client import chat_with_journal_context


def _parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid date format: {value}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the journal assistant.")
    parser.add_argument(
        "--start",
        type=_parse_date,
        required=True,
        help="Start date for the context window (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end",
        type=_parse_date,
        required=True,
        help="End date for the context window (YYYY-MM-DD).",
    )
    args = parser.parse_args()

    if args.start > args.end:
        raise SystemExit("Start date must be on or before end date.")

    print("Journal assistant ready. Type 'exit' or 'quit' to leave.")
    history: list[tuple[str, str]] = []

    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()  # newline for clean exit
            break

        if not question:
            continue

        lower = question.lower()
        if lower in {"exit", "quit"}:
            break

        response = chat_with_journal_context(
            message=question,
            start_date=args.start,
            end_date=args.end,
            history=history,
        )
        print("Assistant:", response)
        history.append((question, response))


if __name__ == "__main__":
    main()

