from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    timezone_display: Mapped[str] = mapped_column(String(64), nullable=False)

    grand_prix: Mapped[list["GrandPrix"]] = relationship("GrandPrix", back_populates="season")


class GrandPrix(Base):
    __tablename__ = "grand_prix"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    starts_at_utc: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    has_sprint: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)

    season: Mapped[Season] = relationship("Season", back_populates="grand_prix")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="grand_prix")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gp_id: Mapped[int] = mapped_column(ForeignKey("grand_prix.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    deadline_utc: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")

    grand_prix: Mapped[GrandPrix] = relationship("GrandPrix", back_populates="sessions")
