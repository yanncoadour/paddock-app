from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session as OrmSession

from app.db import SessionLocal
from app.models import GrandPrix, Season, Session


PARIS_TZ = ZoneInfo("Europe/Paris")

MONTHS = {
    "janv.": 1,
    "févr.": 2,
    "mars": 3,
    "avr.": 4,
    "mai": 5,
    "juin": 6,
    "juil.": 7,
    "août": 8,
    "sept.": 9,
    "oct.": 10,
    "nov.": 11,
    "déc.": 12,
}


@dataclass
class SessionSpec:
    type: str
    local_time: str


@dataclass
class GpSpec:
    round_number: int
    name: str
    sessions: list[SessionSpec]


def parse_paris_datetime(value: str) -> datetime:
    parts = value.strip().split()
    if parts[0].endswith("."):
        parts = parts[1:]
    if len(parts) != 4:
        raise ValueError(f"Format de date invalide: {value}")
    day = int(parts[0])
    month = MONTHS.get(parts[1])
    if not month:
        raise ValueError(f"Mois invalide: {parts[1]}")
    year = int(parts[2])
    hour_str, minute_str = parts[3].split(":")
    local_dt = datetime(year, month, day, int(hour_str), int(minute_str), tzinfo=PARIS_TZ)
    return local_dt.astimezone(timezone.utc)


def split_gp_name(name: str) -> tuple[str, str]:
    if "(" in name and name.endswith(")"):
        base, detail = name.split("(", 1)
        return base.strip(), detail[:-1].strip()
    if "Grand Prix d’" in name:
        return name, name.split("Grand Prix d’", 1)[1].strip()
    if "Grand Prix de " in name:
        return name, name.split("Grand Prix de ", 1)[1].strip()
    return name, name


def upsert_season(session: OrmSession) -> Season:
    season = session.query(Season).filter_by(year=2026).one_or_none()
    if season:
        season.name = "Season 2026"
        season.timezone_display = "Europe/Paris"
        return season
    season = Season(year=2026, name="Season 2026", timezone_display="Europe/Paris")
    session.add(season)
    return season


def upsert_grand_prix(session: OrmSession, season: Season, spec: GpSpec) -> GrandPrix:
    gp = (
        session.query(GrandPrix)
        .filter_by(season_id=season.id, round_number=spec.round_number)
        .one_or_none()
    )
    name, country = split_gp_name(spec.name)
    race_session = next(s for s in spec.sessions if s.type == "RACE")
    starts_at_utc = parse_paris_datetime(race_session.local_time)
    has_sprint = any(s.type in {"SPRINT_QUALI", "SPRINT_RACE"} for s in spec.sessions)
    if gp:
        gp.name = name
        gp.country = country
        gp.starts_at_utc = starts_at_utc
        gp.has_sprint = has_sprint
        return gp
    gp = GrandPrix(
        season_id=season.id,
        name=name,
        country=country,
        starts_at_utc=starts_at_utc,
        has_sprint=has_sprint,
        round_number=spec.round_number,
    )
    session.add(gp)
    return gp


def upsert_session(session: OrmSession, gp: GrandPrix, spec: SessionSpec) -> Session:
    record = session.query(Session).filter_by(gp_id=gp.id, type=spec.type).one_or_none()
    deadline_utc = parse_paris_datetime(spec.local_time)
    if record:
        record.deadline_utc = deadline_utc
        if not record.status:
            record.status = "open"
        return record
    record = Session(gp_id=gp.id, type=spec.type, deadline_utc=deadline_utc, status="open")
    session.add(record)
    return record


def seed_calendar() -> None:
    specs = [
        GpSpec(
            round_number=1,
            name="Grand Prix d’Australie (Melbourne)",
            sessions=[
                SessionSpec("QUALI", "sam. 7 mars 2026 06:00"),
                SessionSpec("RACE", "dim. 8 mars 2026 05:00"),
            ],
        ),
        GpSpec(
            round_number=2,
            name="Grand Prix de Chine (Shanghai)",
            sessions=[
                SessionSpec("SPRINT_QUALI", "ven. 13 mars 2026 08:30"),
                SessionSpec("SPRINT_RACE", "sam. 14 mars 2026 04:00"),
                SessionSpec("QUALI", "sam. 14 mars 2026 08:00"),
                SessionSpec("RACE", "dim. 15 mars 2026 08:00"),
            ],
        ),
        GpSpec(
            round_number=3,
            name="Grand Prix du Japon (Suzuka)",
            sessions=[
                SessionSpec("QUALI", "sam. 28 mars 2026 07:00"),
                SessionSpec("RACE", "dim. 29 mars 2026 07:00"),
            ],
        ),
        GpSpec(
            round_number=4,
            name="Grand Prix de Bahreïn (Sakhir)",
            sessions=[
                SessionSpec("QUALI", "sam. 11 avr. 2026 18:00"),
                SessionSpec("RACE", "dim. 12 avr. 2026 17:00"),
            ],
        ),
        GpSpec(
            round_number=5,
            name="Grand Prix d’Arabie saoudite (Djeddah)",
            sessions=[
                SessionSpec("QUALI", "sam. 18 avr. 2026 19:00"),
                SessionSpec("RACE", "dim. 19 avr. 2026 19:00"),
            ],
        ),
        GpSpec(
            round_number=6,
            name="Grand Prix de Miami",
            sessions=[
                SessionSpec("SPRINT_QUALI", "ven. 1 mai 2026 22:30"),
                SessionSpec("SPRINT_RACE", "sam. 2 mai 2026 18:00"),
                SessionSpec("QUALI", "sam. 2 mai 2026 22:00"),
                SessionSpec("RACE", "dim. 3 mai 2026 22:00"),
            ],
        ),
        GpSpec(
            round_number=7,
            name="Grand Prix du Canada (Montréal)",
            sessions=[
                SessionSpec("SPRINT_QUALI", "ven. 22 mai 2026 22:30"),
                SessionSpec("SPRINT_RACE", "sam. 23 mai 2026 18:00"),
                SessionSpec("QUALI", "sam. 23 mai 2026 22:00"),
                SessionSpec("RACE", "dim. 24 mai 2026 22:00"),
            ],
        ),
        GpSpec(
            round_number=8,
            name="Grand Prix de Monaco",
            sessions=[
                SessionSpec("QUALI", "sam. 6 juin 2026 16:00"),
                SessionSpec("RACE", "dim. 7 juin 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=9,
            name="Grand Prix de Barcelone",
            sessions=[
                SessionSpec("QUALI", "sam. 13 juin 2026 16:00"),
                SessionSpec("RACE", "dim. 14 juin 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=10,
            name="Grand Prix d’Autriche (Spielberg)",
            sessions=[
                SessionSpec("QUALI", "sam. 27 juin 2026 16:00"),
                SessionSpec("RACE", "dim. 28 juin 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=11,
            name="Grand Prix de Grande-Bretagne (Silverstone)",
            sessions=[
                SessionSpec("SPRINT_QUALI", "ven. 3 juil. 2026 17:30"),
                SessionSpec("SPRINT_RACE", "sam. 4 juil. 2026 13:00"),
                SessionSpec("QUALI", "sam. 4 juil. 2026 17:00"),
                SessionSpec("RACE", "dim. 5 juil. 2026 16:00"),
            ],
        ),
        GpSpec(
            round_number=12,
            name="Grand Prix de Belgique (Spa-Francorchamps)",
            sessions=[
                SessionSpec("QUALI", "sam. 18 juil. 2026 16:00"),
                SessionSpec("RACE", "dim. 19 juil. 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=13,
            name="Grand Prix de Hongrie (Budapest)",
            sessions=[
                SessionSpec("QUALI", "sam. 25 juil. 2026 16:00"),
                SessionSpec("RACE", "dim. 26 juil. 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=14,
            name="Grand Prix des Pays-Bas (Zandvoort)",
            sessions=[
                SessionSpec("SPRINT_QUALI", "ven. 21 août 2026 16:30"),
                SessionSpec("SPRINT_RACE", "sam. 22 août 2026 12:00"),
                SessionSpec("QUALI", "sam. 22 août 2026 16:00"),
                SessionSpec("RACE", "dim. 23 août 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=15,
            name="Grand Prix d’Italie (Monza)",
            sessions=[
                SessionSpec("QUALI", "sam. 5 sept. 2026 16:00"),
                SessionSpec("RACE", "dim. 6 sept. 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=16,
            name="Grand Prix de Madrid",
            sessions=[
                SessionSpec("QUALI", "sam. 12 sept. 2026 16:00"),
                SessionSpec("RACE", "dim. 13 sept. 2026 15:00"),
            ],
        ),
        GpSpec(
            round_number=17,
            name="Grand Prix d’Azerbaïdjan (Bakou)",
            sessions=[
                SessionSpec("QUALI", "ven. 25 sept. 2026 14:00"),
                SessionSpec("RACE", "sam. 26 sept. 2026 13:00"),
            ],
        ),
        GpSpec(
            round_number=18,
            name="Grand Prix de Singapour",
            sessions=[
                SessionSpec("SPRINT_QUALI", "ven. 9 oct. 2026 14:30"),
                SessionSpec("SPRINT_RACE", "sam. 10 oct. 2026 11:00"),
                SessionSpec("QUALI", "sam. 10 oct. 2026 15:00"),
                SessionSpec("RACE", "dim. 11 oct. 2026 14:00"),
            ],
        ),
        GpSpec(
            round_number=19,
            name="Grand Prix des États-Unis (Austin)",
            sessions=[
                SessionSpec("QUALI", "sam. 24 oct. 2026 23:00"),
                SessionSpec("RACE", "dim. 25 oct. 2026 21:00"),
            ],
        ),
        GpSpec(
            round_number=20,
            name="Grand Prix du Mexique (Mexico)",
            sessions=[
                SessionSpec("QUALI", "sam. 31 oct. 2026 22:00"),
                SessionSpec("RACE", "dim. 1 nov. 2026 21:00"),
            ],
        ),
        GpSpec(
            round_number=21,
            name="Grand Prix du Brésil (São Paulo)",
            sessions=[
                SessionSpec("QUALI", "sam. 7 nov. 2026 19:00"),
                SessionSpec("RACE", "dim. 8 nov. 2026 18:00"),
            ],
        ),
        GpSpec(
            round_number=22,
            name="Grand Prix de Las Vegas",
            sessions=[
                SessionSpec("QUALI", "sam. 21 nov. 2026 05:00"),
                SessionSpec("RACE", "dim. 22 nov. 2026 05:00"),
            ],
        ),
        GpSpec(
            round_number=23,
            name="Grand Prix du Qatar (Lusail)",
            sessions=[
                SessionSpec("QUALI", "sam. 28 nov. 2026 19:00"),
                SessionSpec("RACE", "dim. 29 nov. 2026 17:00"),
            ],
        ),
        GpSpec(
            round_number=24,
            name="Grand Prix d’Abou Dhabi",
            sessions=[
                SessionSpec("QUALI", "sam. 5 déc. 2026 15:00"),
                SessionSpec("RACE", "dim. 6 déc. 2026 14:00"),
            ],
        ),
    ]

    with SessionLocal() as session:
        season = upsert_season(session)
        session.flush()

        for spec in specs:
            gp = upsert_grand_prix(session, season, spec)
            session.flush()
            for session_spec in spec.sessions:
                upsert_session(session, gp, session_spec)

        session.commit()


if __name__ == "__main__":
    seed_calendar()
