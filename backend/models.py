"""
ORM models for journaling data.
"""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .db import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_date = Column(Date, nullable=False)
    source_path = Column(String(255), nullable=True, unique=True)
    file_hash = Column(String(64), nullable=True)
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    entry_metadata = relationship(
        "JournalMetadata",
        back_populates="entry",
        cascade="all, delete-orphan",
        uselist=False,
    )
    events = relationship(
        "Event",
        back_populates="entry",
        cascade="all, delete-orphan",
    )


class JournalMetadata(Base):
    __tablename__ = "journal_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    mood_score = Column(Integer, nullable=False, default=5)
    energy_score = Column(Integer, nullable=False, default=5)
    stress_score = Column(Integer, nullable=False, default=5)
    sleep_hours = Column(Float, nullable=False, default=7.0)

    entry = relationship("JournalEntry", back_populates="entry_metadata")


class Event(Base):
    __tablename__ = "journal_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(32), nullable=False, default="other")
    effect_on_mood = Column(Integer, nullable=False, default=0)

    entry = relationship("JournalEntry", back_populates="events")
    people = relationship(
        "Person",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class Person(Base):
    __tablename__ = "journal_event_people"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("journal_events.id"), nullable=False)
    name = Column(String(128), nullable=False)

    event = relationship("Event", back_populates="people")

