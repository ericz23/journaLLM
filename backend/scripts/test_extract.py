import sys
from pathlib import Path
from backend.services.gemini_client import extract_journal_metadata

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m backend.scripts.test_extract path/to/journal.md")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    data = extract_journal_metadata(text)
    print("Extracted JSON:")
    import pprint
    pprint.pprint(data)


if __name__ == "__main__":
    main()