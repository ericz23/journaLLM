"""
Utility to initialize the SQLite database with all tables.
"""

from backend.config import DATABASE_URL
from backend.db import init_db

# Import models so they register with SQLAlchemy's metadata before init_db runs.
import backend.models  # noqa: F401


def main() -> None:
    init_db()
    print(f"Database initialized at {DATABASE_URL}")


if __name__ == "__main__":
    main()

