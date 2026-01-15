import os
import secrets
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text

from app.auth import (
    create_access_token,
    decode_token,
    hash_password,
    is_beta_allowed,
    verify_password,
)
from app.db import get_engine

app = FastAPI(title="Paddock API")
engine = get_engine()
security = HTTPBearer()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: str


class PaddockCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    season_year: int = Field(ge=2000, le=2100)


class PaddockJoinRequest(BaseModel):
    join_code: str


class PaddockResponse(BaseModel):
    id: int
    name: str
    join_code: str
    season_year: int
    status: str
    role: str


class SeasonResponse(BaseModel):
    id: int
    year: int
    name: str
    timezone_display: str


class SessionResponse(BaseModel):
    id: int
    type: str
    deadline_utc: datetime
    status: str


class GrandPrixResponse(BaseModel):
    id: int
    season_id: int
    name: str
    country: str
    starts_at_utc: datetime
    has_sprint: bool
    round_number: int


class GrandPrixDetailResponse(GrandPrixResponse):
    sessions: list[SessionResponse]


class PickCreateRequest(BaseModel):
    paddock_id: int
    type: str
    positions: list[str]


class PickResponse(BaseModel):
    id: int
    user_id: int
    paddock_id: int
    session_id: int
    type: str
    positions: list[int]
    submitted_at_utc: datetime


class QuizResponse(BaseModel):
    id: int
    season_id: int | None
    gp_id: int | None
    scope: str
    title: str
    is_open: bool


class QuizAnswerItem(BaseModel):
    question_id: int
    choice_id: str


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswerItem]


class QuizAnswerResponse(BaseModel):
    question_id: int
    choice_id: str
    submitted_at_utc: datetime


class CardResponse(BaseModel):
    id: int
    code: str
    label: str
    value: int
    type: str
    uses: list[dict[str, int | str]]


class CardUseRequest(BaseModel):
    paddock_id: int
    target_user_id: int


class GpScoreResponse(BaseModel):
    id: int
    gp_id: int
    user_id: int
    score_brut: int
    calculated_at_utc: datetime


class StandingResponse(BaseModel):
    id: int
    gp_id: int
    user_id: int
    rank: int
    points: float


class StandingsComputeRequest(BaseModel):
    scope: str = "GP"
    points: list[int] | None = None


class SeasonStandingsComputeRequest(BaseModel):
    paddock_id: int


class SeasonStandingResponse(BaseModel):
    id: int
    season_id: int
    paddock_id: int
    user_id: int
    rank: int
    points_total: float


def is_beta_mode() -> bool:
    return os.getenv("BETA_MODE", "false").lower() == "true"


def require_beta_allowed(email: str) -> None:
    if is_beta_mode() and not is_beta_allowed(engine, email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Beta privée")


@app.post("/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    require_beta_allowed(payload.email)
    password_hash = hash_password(payload.password)

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM users WHERE email = :email"),
            {"email": payload.email},
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")

        result = conn.execute(
            text(
                """
                INSERT INTO users (email, password_hash, display_name)
                VALUES (:email, :password_hash, :display_name)
                RETURNING id
                """
            ),
            {
                "email": payload.email,
                "password_hash": password_hash,
                "display_name": payload.display_name,
            },
        )
        user_id = result.scalar_one()

    token = create_access_token(str(user_id))
    return AuthResponse(access_token=token)


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    require_beta_allowed(payload.email)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT id, password_hash
                FROM users
                WHERE email = :email
                """
            ),
            {"email": payload.email},
        ).first()

    if not result or not verify_password(payload.password, result.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    token = create_access_token(str(result.id))
    return AuthResponse(access_token=token)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserResponse:
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide") from None

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT id, email, display_name
                FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        ).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

    return UserResponse(id=result.id, email=result.email, display_name=result.display_name)


@app.get("/me", response_model=UserResponse)
def me(current_user: Annotated[UserResponse, Depends(get_current_user)]) -> UserResponse:
    return current_user


def generate_join_code() -> str:
    return secrets.token_hex(4).upper()


def get_paddock_by_id(paddock_id: int) -> dict[str, str | int] | None:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT id, name, join_code, season_year, status, owner_id
                FROM paddocks
                WHERE id = :paddock_id
                """
            ),
            {"paddock_id": paddock_id},
        ).mappings().first()
        return dict(result) if result else None


def get_member_role(user_id: int, paddock_id: int) -> str | None:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT role
                FROM paddock_members
                WHERE user_id = :user_id AND paddock_id = :paddock_id
                """
            ),
            {"user_id": user_id, "paddock_id": paddock_id},
        ).first()
        return result.role if result else None


def normalize_driver_code(code: str) -> int:
    normalized = code.strip().upper()
    if not normalized.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code pilote invalide")
    return int(normalized)


def normalize_driver_codes(codes: list[str]) -> list[int]:
    return [normalize_driver_code(code) for code in codes]


@app.post("/paddocks", response_model=PaddockResponse)
def create_paddock(
    payload: PaddockCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> PaddockResponse:
    join_code = generate_join_code()
    with engine.begin() as conn:
        while True:
            existing = conn.execute(
                text("SELECT 1 FROM paddocks WHERE join_code = :join_code"),
                {"join_code": join_code},
            ).first()
            if not existing:
                break
            join_code = generate_join_code()

        result = conn.execute(
            text(
                """
                INSERT INTO paddocks (name, owner_id, join_code, season_year, status)
                VALUES (:name, :owner_id, :join_code, :season_year, 'draft')
                RETURNING id, name, join_code, season_year, status
                """
            ),
            {
                "name": payload.name,
                "owner_id": current_user.id,
                "join_code": join_code,
                "season_year": payload.season_year,
            },
        ).mappings().one()

        conn.execute(
            text(
                """
                INSERT INTO paddock_members (user_id, paddock_id, role)
                VALUES (:user_id, :paddock_id, 'owner')
                """
            ),
            {"user_id": current_user.id, "paddock_id": result["id"]},
        )

    return PaddockResponse(**result, role="owner")


@app.post("/paddocks/join", response_model=PaddockResponse)
def join_paddock(
    payload: PaddockJoinRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> PaddockResponse:
    with engine.begin() as conn:
        paddock = conn.execute(
            text(
                """
                SELECT id, name, join_code, season_year, status, owner_id
                FROM paddocks
                WHERE join_code = :join_code
                """
            ),
            {"join_code": payload.join_code},
        ).mappings().first()

        if not paddock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paddock introuvable")

        if paddock["status"] != "open":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Paddock fermé")

        role = conn.execute(
            text(
                """
                SELECT role
                FROM paddock_members
                WHERE user_id = :user_id AND paddock_id = :paddock_id
                """
            ),
            {"user_id": current_user.id, "paddock_id": paddock["id"]},
        ).first()

        if not role:
            conn.execute(
                text(
                    """
                    INSERT INTO paddock_members (user_id, paddock_id, role)
                    VALUES (:user_id, :paddock_id, 'member')
                    """
                ),
                {"user_id": current_user.id, "paddock_id": paddock["id"]},
            )
            role_value = "member"
        else:
            role_value = role.role

    return PaddockResponse(
        id=paddock["id"],
        name=paddock["name"],
        join_code=paddock["join_code"],
        season_year=paddock["season_year"],
        status=paddock["status"],
        role=role_value,
    )


@app.get("/paddocks", response_model=list[PaddockResponse])
def list_paddocks(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[PaddockResponse]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT p.id, p.name, p.join_code, p.season_year, p.status, pm.role
                FROM paddocks p
                JOIN paddock_members pm ON pm.paddock_id = p.id
                WHERE pm.user_id = :user_id
                ORDER BY p.season_year DESC, p.created_at DESC
                """
            ),
            {"user_id": current_user.id},
        ).mappings()

        return [PaddockResponse(**row) for row in rows]


@app.get("/paddocks/{paddock_id}", response_model=PaddockResponse)
def get_paddock(
    paddock_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> PaddockResponse:
    paddock = get_paddock_by_id(paddock_id)
    if not paddock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paddock introuvable")

    role = get_member_role(current_user.id, paddock_id)
    if paddock["status"] == "draft" and paddock["owner_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paddock introuvable")

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paddock introuvable")

    return PaddockResponse(
        id=paddock["id"],
        name=paddock["name"],
        join_code=paddock["join_code"],
        season_year=paddock["season_year"],
        status=paddock["status"],
        role=role,
    )


@app.post("/paddocks/{paddock_id}/lock", response_model=PaddockResponse)
def lock_paddock(
    paddock_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> PaddockResponse:
    paddock = get_paddock_by_id(paddock_id)
    if not paddock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paddock introuvable")

    if paddock["owner_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    with engine.begin() as conn:
        updated = conn.execute(
            text(
                """
                UPDATE paddocks
                SET status = 'locked'
                WHERE id = :paddock_id
                RETURNING id, name, join_code, season_year, status
                """
            ),
            {"paddock_id": paddock_id},
        ).mappings().one()

    return PaddockResponse(**updated, role="owner")


@app.get("/seasons/current", response_model=SeasonResponse)
def get_current_season() -> SeasonResponse:
    with engine.connect() as conn:
        season = conn.execute(
            text(
                """
                SELECT id, year, name, timezone_display
                FROM seasons
                ORDER BY year DESC
                LIMIT 1
                """
            )
        ).mappings().first()

    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saison introuvable")

    return SeasonResponse(**season)


@app.get("/gps", response_model=list[GrandPrixResponse])
def list_grand_prix(season_year: int) -> list[GrandPrixResponse]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT gp.id,
                       gp.season_id,
                       gp.name,
                       gp.country,
                       gp.starts_at_utc,
                       gp.has_sprint,
                       gp.round_number
                FROM grand_prix gp
                JOIN seasons s ON s.id = gp.season_id
                WHERE s.year = :season_year
                ORDER BY gp.round_number ASC
                """
            ),
            {"season_year": season_year},
        ).mappings()

        return [GrandPrixResponse(**row) for row in rows]


@app.get("/gps/{gp_id}", response_model=GrandPrixDetailResponse)
def get_grand_prix(gp_id: int) -> GrandPrixDetailResponse:
    with engine.connect() as conn:
        gp = conn.execute(
            text(
                """
                SELECT id,
                       season_id,
                       name,
                       country,
                       starts_at_utc,
                       has_sprint,
                       round_number
                FROM grand_prix
                WHERE id = :gp_id
                """
            ),
            {"gp_id": gp_id},
        ).mappings().first()

        if not gp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grand Prix introuvable")

        sessions = conn.execute(
            text(
                """
                SELECT id, type, deadline_utc, status
                FROM sessions
                WHERE gp_id = :gp_id
                ORDER BY deadline_utc ASC
                """
            ),
            {"gp_id": gp_id},
        ).mappings()

    return GrandPrixDetailResponse(**gp, sessions=[SessionResponse(**row) for row in sessions])


def require_paddock_member(user_id: int, paddock_id: int) -> None:
    role = get_member_role(user_id, paddock_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")


def get_session_or_404(session_id: int) -> dict[str, str | int | datetime]:
    with engine.connect() as conn:
        session = conn.execute(
            text(
                """
                SELECT id, gp_id, type, deadline_utc, status
                FROM sessions
                WHERE id = :session_id
                """
            ),
            {"session_id": session_id},
        ).mappings().first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")

    return dict(session)


def validate_pick_payload(payload: PickCreateRequest, session: dict[str, str | int | datetime]) -> list[int]:
    if payload.type not in {"TOP10", "TOP8"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type de pronostic invalide")

    normalized_positions = normalize_driver_codes(payload.positions)
    expected_size = 10 if payload.type == "TOP10" else 8
    if len(normalized_positions) != expected_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Taille de pronostic invalide")

    if len(set(normalized_positions)) != len(normalized_positions):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Positions dupliquées")

    if session["status"] != "open":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session verrouillée")

    deadline = session["deadline_utc"]
    now = datetime.now(timezone.utc)
    if isinstance(deadline, datetime) and deadline <= now:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deadline dépassée")

    return normalized_positions


def quiz_deadline_utc(quiz: dict[str, str | int | None]) -> datetime | None:
    if quiz["scope"] == "PRESEASON":
        return None

    if not quiz.get("gp_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz invalide")

    session_type = "QUALI" if quiz["scope"] == "GP" else "SPRINT_QUALI"
    with engine.connect() as conn:
        session = conn.execute(
            text(
                """
                SELECT deadline_utc
                FROM sessions
                WHERE gp_id = :gp_id AND type = :session_type
                """
            ),
            {"gp_id": quiz["gp_id"], "session_type": session_type},
        ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")

    return session.deadline_utc


def require_quiz_open(quiz: dict[str, str | int | None]) -> None:
    if not quiz["is_open"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Quiz verrouillé")

    deadline = quiz_deadline_utc(quiz)
    if deadline and deadline <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Quiz verrouillé")


def get_quiz_or_404(quiz_id: int) -> dict[str, str | int | None]:
    with engine.connect() as conn:
        quiz = conn.execute(
            text(
                """
                SELECT id, season_id, gp_id, scope, title, is_open
                FROM quizzes
                WHERE id = :quiz_id
                """
            ),
            {"quiz_id": quiz_id},
        ).mappings().first()

    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz introuvable")

    return dict(quiz)


def get_gp_race_session(gp_id: int) -> dict[str, str | datetime]:
    with engine.connect() as conn:
        session = conn.execute(
            text(
                """
                SELECT type, status, deadline_utc
                FROM sessions
                WHERE gp_id = :gp_id AND type = 'RACE'
                """
            ),
            {"gp_id": gp_id},
        ).mappings().first()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")

    return dict(session)


def require_card_target_valid(payload: CardUseRequest, card_type: str, current_user_id: int) -> None:
    if card_type == "BONUS" and payload.target_user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cible invalide")

    if card_type == "MALUS" and payload.target_user_id == current_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cible invalide")


def fetch_session_results(session_ids: list[int]) -> dict[int, list[int]]:
    if not session_ids:
        return {}

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT session_id, positions
                FROM session_results
                WHERE session_id = ANY(:session_ids)
                """
            ),
            {"session_ids": session_ids},
        ).mappings()

    return {row["session_id"]: list(row["positions"]) for row in rows}


def score_positions(
    predicted: list[int],
    results: list[int],
    top_range: range,
    points_top: dict[int, int],
    points_bottom: dict[int, int],
) -> int:
    score = 0
    result_index = {driver_id: idx + 1 for idx, driver_id in enumerate(results)}
    for position, driver_id in enumerate(predicted, start=1):
        actual_position = result_index.get(driver_id)
        if actual_position is None:
            continue
        delta = abs(position - actual_position)
        if delta > 2:
            continue
        if position in top_range:
            score += points_top.get(delta, 0)
        else:
            score += points_bottom.get(delta, 0)
    return score


def score_sport_for_session(session_type: str, predicted: list[int], results: list[int]) -> int:
    if session_type == "QUALI":
        return score_positions(
            predicted,
            results,
            range(1, 4),
            {0: 25, 1: 18, 2: 10},
            {0: 25, 1: 18, 2: 10},
        )
    if session_type == "RACE":
        return score_positions(
            predicted,
            results,
            range(1, 4),
            {0: 60, 1: 40, 2: 20},
            {0: 40, 1: 25, 2: 15},
        )
    if session_type == "SPRINT_QUALI":
        return score_positions(
            predicted,
            results,
            range(1, 4),
            {0: 10, 1: 7, 2: 4},
            {0: 6, 1: 4, 2: 2},
        )
    if session_type == "SPRINT_RACE":
        return score_positions(
            predicted,
            results,
            range(1, 4),
            {0: 30, 1: 20, 2: 10},
            {0: 10, 1: 7, 2: 4},
        )
    return 0


def score_qcm_for_gp(gp_id: int) -> dict[int, int]:
    with engine.connect() as conn:
        quizzes = conn.execute(
            text(
                """
                SELECT id, scope
                FROM quizzes
                WHERE gp_id = :gp_id AND scope IN ('GP', 'SPRINT')
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

        if not quizzes:
            return {}

        quiz_ids = [quiz["id"] for quiz in quizzes]
        scope_by_quiz = {quiz["id"]: quiz["scope"] for quiz in quizzes}

        correct_choices = conn.execute(
            text(
                """
                SELECT qc.question_id, qc.choice_id
                FROM quiz_correct_choices qc
                JOIN quiz_questions qq ON qq.id = qc.question_id
                WHERE qq.quiz_id = ANY(:quiz_ids)
                """
            ),
            {"quiz_ids": quiz_ids},
        ).mappings().all()

        correct_by_question: dict[int, set[str]] = {}
        for row in correct_choices:
            correct_by_question.setdefault(row["question_id"], set()).add(row["choice_id"])

        answers = conn.execute(
            text(
                """
                SELECT qa.user_id, qa.question_id, qa.choice_id, qq.quiz_id
                FROM quiz_answers qa
                JOIN quiz_questions qq ON qq.id = qa.question_id
                WHERE qq.quiz_id = ANY(:quiz_ids)
                """
            ),
            {"quiz_ids": quiz_ids},
        ).mappings().all()

    scores: dict[int, int] = {}
    for answer in answers:
        user_id = answer["user_id"]
        question_id = answer["question_id"]
        quiz_id = answer["quiz_id"]
        if answer["choice_id"] not in correct_by_question.get(question_id, set()):
            continue
        scope = scope_by_quiz.get(quiz_id, "GP")
        points = 10 if scope in {"GP", "SPRINT"} else 60
        scores[user_id] = scores.get(user_id, 0) + points

    return scores


def score_bonus_for_gp(gp_id: int) -> dict[int, int]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT bu.played_by_user_id, bc.type, bc.value
                FROM bonus_uses bu
                JOIN bonus_cards bc ON bc.id = bu.card_id
                WHERE bu.gp_id = :gp_id
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

    scores: dict[int, int] = {}
    for row in rows:
        user_id = row["played_by_user_id"]
        value = int(row["value"])
        if row["type"] == "MALUS":
            scores[user_id] = scores.get(user_id, 0) - value
        else:
            scores[user_id] = scores.get(user_id, 0) + value
    return scores


def score_sport_for_gp(gp_id: int) -> dict[int, int]:
    with engine.connect() as conn:
        sessions = conn.execute(
            text(
                """
                SELECT id, type
                FROM sessions
                WHERE gp_id = :gp_id
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

        if not sessions:
            return {}

        session_type_by_id = {session["id"]: session["type"] for session in sessions}
        session_ids = list(session_type_by_id.keys())
        results_by_session = fetch_session_results(session_ids)

        picks = conn.execute(
            text(
                """
                SELECT user_id, session_id, positions
                FROM picks
                WHERE session_id = ANY(:session_ids)
                """
            ),
            {"session_ids": session_ids},
        ).mappings().all()

    scores: dict[int, int] = {}
    for pick in picks:
        session_id = pick["session_id"]
        results = results_by_session.get(session_id)
        if not results:
            continue
        session_type = session_type_by_id.get(session_id, "")
        score = score_sport_for_session(session_type, list(pick["positions"]), results)
        user_id = pick["user_id"]
        scores[user_id] = scores.get(user_id, 0) + score

    return scores


def get_points_scale(scope: str, custom_points: list[int] | None) -> list[int]:
    if custom_points is not None:
        if not custom_points:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barème invalide")
        if any(point < 0 for point in custom_points):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barème invalide")
        return custom_points

    if scope == "SPRINT":
        return [8, 7, 6, 5, 4, 3, 2, 1]
    return [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def compute_dense_ranks(scores: list[dict[str, int]]) -> list[dict[str, int]]:
    if not scores:
        return []

    ranked: list[dict[str, int]] = []
    rank = 0
    previous_score = None
    for row in scores:
        score = row["score_brut"]
        if previous_score is None or score != previous_score:
            rank += 1
            previous_score = score
        ranked.append({**row, "rank": rank})

    return ranked


def compute_dense_ranks_by_key(rows: list[dict[str, int | float]], key: str) -> list[dict[str, int | float]]:
    if not rows:
        return []

    ranked: list[dict[str, int | float]] = []
    rank = 0
    previous_value: int | float | None = None
    for row in rows:
        value = row[key]
        if previous_value is None or value != previous_value:
            rank += 1
            previous_value = value
        ranked.append({**row, "rank": rank})

    return ranked


@app.post("/picks/{session_id}", response_model=PickResponse)
def create_pick(
    session_id: int,
    payload: PickCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> PickResponse:
    session = get_session_or_404(session_id)
    require_paddock_member(current_user.id, payload.paddock_id)
    normalized_positions = validate_pick_payload(payload, session)

    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT id
                FROM picks
                WHERE user_id = :user_id AND session_id = :session_id
                """
            ),
            {"user_id": current_user.id, "session_id": session_id},
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pronostic déjà soumis")

        result = conn.execute(
            text(
                """
                INSERT INTO picks (user_id, paddock_id, session_id, type, positions, submitted_at_utc)
                VALUES (:user_id, :paddock_id, :session_id, :type, :positions, now())
                RETURNING id, user_id, paddock_id, session_id, type, positions, submitted_at_utc
                """
            ),
            {
                "user_id": current_user.id,
                "paddock_id": payload.paddock_id,
                "session_id": session_id,
                "type": payload.type,
                "positions": normalized_positions,
            },
        ).mappings().one()

    return PickResponse(**result)


@app.get("/picks/{session_id}/me", response_model=PickResponse)
def get_my_pick(
    session_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> PickResponse:
    with engine.connect() as conn:
        pick = conn.execute(
            text(
                """
                SELECT id, user_id, paddock_id, session_id, type, positions, submitted_at_utc
                FROM picks
                WHERE user_id = :user_id AND session_id = :session_id
                """
            ),
            {"user_id": current_user.id, "session_id": session_id},
        ).mappings().first()

    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pronostic introuvable")

    require_paddock_member(current_user.id, pick["paddock_id"])
    return PickResponse(**pick)


@app.get("/paddocks/{paddock_id}/picks/{session_id}", response_model=list[PickResponse])
def list_paddock_picks(
    paddock_id: int,
    session_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[PickResponse]:
    require_paddock_member(current_user.id, paddock_id)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, user_id, paddock_id, session_id, type, positions, submitted_at_utc
                FROM picks
                WHERE paddock_id = :paddock_id AND session_id = :session_id
                ORDER BY submitted_at_utc ASC
                """
            ),
            {"paddock_id": paddock_id, "session_id": session_id},
        ).mappings()

    return [PickResponse(**row) for row in rows]


@app.get("/quizzes/open", response_model=list[QuizResponse])
def list_open_quizzes() -> list[QuizResponse]:
    with engine.connect() as conn:
        quizzes = conn.execute(
            text(
                """
                SELECT id, season_id, gp_id, scope, title, is_open
                FROM quizzes
                WHERE is_open = true
                ORDER BY id ASC
                """
            )
        ).mappings().all()

    open_quizzes: list[QuizResponse] = []
    for quiz in quizzes:
        quiz_data = dict(quiz)
        try:
            deadline = quiz_deadline_utc(quiz_data)
        except HTTPException:
            continue
        if deadline and deadline <= datetime.now(timezone.utc):
            continue
        open_quizzes.append(QuizResponse(**quiz_data))

    return open_quizzes


@app.post("/quizzes/{quiz_id}/submit", response_model=list[QuizAnswerResponse])
def submit_quiz(
    quiz_id: int,
    payload: QuizSubmitRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[QuizAnswerResponse]:
    quiz = get_quiz_or_404(quiz_id)
    require_quiz_open(quiz)

    if not payload.answers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Réponses manquantes")

    question_ids = [answer.question_id for answer in payload.answers]
    if len(question_ids) != len(set(question_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Questions dupliquées")

    with engine.begin() as conn:
        existing = conn.execute(
            text(
                """
                SELECT 1
                FROM quiz_answers
                WHERE user_id = :user_id AND quiz_id = :quiz_id
                LIMIT 1
                """
            ),
            {"user_id": current_user.id, "quiz_id": quiz_id},
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Quiz déjà soumis")

        valid_questions = conn.execute(
            text(
                """
                SELECT id
                FROM quiz_questions
                WHERE quiz_id = :quiz_id
                """
            ),
            {"quiz_id": quiz_id},
        ).scalars().all()

        if not valid_questions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz invalide")

        valid_question_set = set(valid_questions)
        for question_id in question_ids:
            if question_id not in valid_question_set:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question invalide")

        valid_choices = conn.execute(
            text(
                """
                SELECT question_id, choice_id
                FROM quiz_choices
                WHERE question_id = ANY(:question_ids)
                """
            ),
            {"question_ids": question_ids},
        ).mappings().all()

        valid_choice_map: dict[int, set[str]] = {}
        for row in valid_choices:
            valid_choice_map.setdefault(row["question_id"], set()).add(row["choice_id"])

        answers_payload: list[dict[str, object]] = []
        for answer in payload.answers:
            valid_for_question = valid_choice_map.get(answer.question_id, set())
            if answer.choice_id not in valid_for_question:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choix invalide")
            answers_payload.append(
                {
                    "user_id": current_user.id,
                    "quiz_id": quiz_id,
                    "question_id": answer.question_id,
                    "choice_id": answer.choice_id,
                }
            )

        conn.execute(
            text(
                """
                INSERT INTO quiz_answers (user_id, quiz_id, question_id, choice_id, submitted_at_utc)
                VALUES (:user_id, :quiz_id, :question_id, :choice_id, now())
                """
            ),
            answers_payload,
        )

        rows = conn.execute(
            text(
                """
                SELECT question_id, choice_id, submitted_at_utc
                FROM quiz_answers
                WHERE user_id = :user_id AND quiz_id = :quiz_id
                ORDER BY submitted_at_utc ASC
                """
            ),
            {"user_id": current_user.id, "quiz_id": quiz_id},
        ).mappings().all()

    return [QuizAnswerResponse(**row) for row in rows]


@app.get("/quizzes/{quiz_id}/me", response_model=list[QuizAnswerResponse])
def get_my_quiz_answers(
    quiz_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[QuizAnswerResponse]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT question_id, choice_id, submitted_at_utc
                FROM quiz_answers
                WHERE user_id = :user_id AND quiz_id = :quiz_id
                ORDER BY submitted_at_utc ASC
                """
            ),
            {"user_id": current_user.id, "quiz_id": quiz_id},
        ).mappings().all()

    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz non soumis")

    return [QuizAnswerResponse(**row) for row in rows]


@app.get("/cards/me", response_model=list[CardResponse])
def list_my_cards(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[CardResponse]:
    with engine.connect() as conn:
        cards = conn.execute(
            text(
                """
                SELECT id, code, label, value, type
                FROM bonus_cards
                ORDER BY id ASC
                """
            )
        ).mappings().all()

        uses = conn.execute(
            text(
                """
                SELECT card_id, gp_id, used_at_utc, season_half
                FROM bonus_uses
                WHERE played_by_user_id = :user_id
                ORDER BY used_at_utc ASC
                """
            ),
            {"user_id": current_user.id},
        ).mappings().all()

    uses_by_card: dict[int, list[dict[str, int | str]]] = {}
    for row in uses:
        uses_by_card.setdefault(row["card_id"], []).append(
            {
                "gp_id": row["gp_id"],
                "used_at_utc": row["used_at_utc"].isoformat(),
                "season_half": row["season_half"],
            }
        )

    return [
        CardResponse(
            id=card["id"],
            code=card["code"],
            label=card["label"],
            value=card["value"],
            type=card["type"],
            uses=uses_by_card.get(card["id"], []),
        )
        for card in cards
    ]


@app.post("/cards/{card_id}/use/{gp_id}")
def use_card(
    card_id: int,
    gp_id: int,
    payload: CardUseRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> dict[str, int | str]:
    require_paddock_member(current_user.id, payload.paddock_id)
    require_paddock_member(payload.target_user_id, payload.paddock_id)

    with engine.begin() as conn:
        card = conn.execute(
            text(
                """
                SELECT id, type
                FROM bonus_cards
                WHERE id = :card_id
                """
            ),
            {"card_id": card_id},
        ).mappings().first()

        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carte introuvable")

        require_card_target_valid(payload, card["type"], current_user.id)

        existing = conn.execute(
            text(
                """
                SELECT 1
                FROM bonus_uses
                WHERE card_id = :card_id AND played_by_user_id = :user_id AND gp_id = :gp_id
                """
            ),
            {"card_id": card_id, "user_id": current_user.id, "gp_id": gp_id},
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Carte déjà utilisée")

        race_session = get_gp_race_session(gp_id)
        if race_session["status"] == "results":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="GP terminé")

        if race_session["deadline_utc"] <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deadline dépassée")

        conn.execute(
            text(
                """
                INSERT INTO bonus_uses (
                    card_id,
                    gp_id,
                    session_type,
                    played_by_user_id,
                    target_user_id,
                    season_half,
                    used_at_utc
                )
                VALUES (:card_id, :gp_id, 'RACE', :played_by_user_id, :target_user_id, 1, now())
                """
            ),
            {
                "card_id": card_id,
                "gp_id": gp_id,
                "played_by_user_id": current_user.id,
                "target_user_id": payload.target_user_id,
            },
        )

    return {"status": "ok"}


@app.post("/scores/recalculate/{gp_id}", response_model=list[GpScoreResponse])
def recalculate_scores(
    gp_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[GpScoreResponse]:
    del current_user
    sport_scores = score_sport_for_gp(gp_id)
    qcm_scores = score_qcm_for_gp(gp_id)
    bonus_scores = score_bonus_for_gp(gp_id)

    user_ids = set(sport_scores) | set(qcm_scores) | set(bonus_scores)
    if not user_ids:
        return []

    scored_rows: list[dict[str, int]] = []
    for user_id in user_ids:
        score_brut = sport_scores.get(user_id, 0) + qcm_scores.get(user_id, 0) + bonus_scores.get(user_id, 0)
        score_brut = max(0, score_brut)
        scored_rows.append({"gp_id": gp_id, "user_id": user_id, "score_brut": score_brut})

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO gp_scores (gp_id, user_id, score_brut, calculated_at_utc)
                VALUES (:gp_id, :user_id, :score_brut, now())
                ON CONFLICT (gp_id, user_id)
                DO UPDATE SET score_brut = EXCLUDED.score_brut,
                              calculated_at_utc = EXCLUDED.calculated_at_utc
                """
            ),
            scored_rows,
        )

        rows = conn.execute(
            text(
                """
                SELECT id, gp_id, user_id, score_brut, calculated_at_utc
                FROM gp_scores
                WHERE gp_id = :gp_id
                ORDER BY user_id ASC
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

    return [GpScoreResponse(**row) for row in rows]


@app.get("/scores/gp/{gp_id}", response_model=list[GpScoreResponse])
def get_gp_scores(
    gp_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[GpScoreResponse]:
    del current_user
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, gp_id, user_id, score_brut, calculated_at_utc
                FROM gp_scores
                WHERE gp_id = :gp_id
                ORDER BY user_id ASC
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

    return [GpScoreResponse(**row) for row in rows]


@app.post("/standings/gp/{gp_id}/compute", response_model=list[StandingResponse])
def compute_gp_standings(
    gp_id: int,
    payload: StandingsComputeRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[StandingResponse]:
    del current_user
    scope = payload.scope.upper()
    if scope not in {"GP", "SPRINT"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scope invalide")

    points_scale = get_points_scale(scope, payload.points)

    with engine.begin() as conn:
        scores = conn.execute(
            text(
                """
                SELECT user_id, score_brut
                FROM gp_scores
                WHERE gp_id = :gp_id
                ORDER BY score_brut DESC, user_id ASC
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

        ranked = compute_dense_ranks([{"user_id": row["user_id"], "score_brut": row["score_brut"]} for row in scores])
        standings_payload: list[dict[str, int | float]] = []
        for row in ranked:
            rank = row["rank"]
            points = points_scale[rank - 1] if rank <= len(points_scale) else 0
            standings_payload.append(
                {
                    "gp_id": gp_id,
                    "user_id": row["user_id"],
                    "rank": rank,
                    "points": points,
                }
            )

        if standings_payload:
            conn.execute(
                text(
                    """
                    INSERT INTO gp_standings (gp_id, user_id, rank, points)
                    VALUES (:gp_id, :user_id, :rank, :points)
                    ON CONFLICT (gp_id, user_id)
                    DO UPDATE SET rank = EXCLUDED.rank,
                                  points = EXCLUDED.points
                    """
                ),
                standings_payload,
            )

        rows = conn.execute(
            text(
                """
                SELECT id, gp_id, user_id, rank, points
                FROM gp_standings
                WHERE gp_id = :gp_id
                ORDER BY rank ASC, user_id ASC
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

    return [StandingResponse(**row) for row in rows]


@app.get("/standings/gp/{gp_id}", response_model=list[StandingResponse])
def get_gp_standings(
    gp_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[StandingResponse]:
    del current_user
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, gp_id, user_id, rank, points
                FROM gp_standings
                WHERE gp_id = :gp_id
                ORDER BY rank ASC, user_id ASC
                """
            ),
            {"gp_id": gp_id},
        ).mappings().all()

    return [StandingResponse(**row) for row in rows]


@app.post("/standings/season/{season_id}/compute", response_model=list[SeasonStandingResponse])
def compute_season_standings(
    season_id: int,
    payload: SeasonStandingsComputeRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[SeasonStandingResponse]:
    require_paddock_member(current_user.id, payload.paddock_id)

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT pm.user_id,
                       COALESCE(SUM(gs.points), 0) AS points_total
                FROM paddock_members pm
                LEFT JOIN gp_standings gs
                    ON gs.user_id = pm.user_id
                LEFT JOIN grand_prix gp
                    ON gp.id = gs.gp_id AND gp.season_id = :season_id
                WHERE pm.paddock_id = :paddock_id
                GROUP BY pm.user_id
                ORDER BY points_total DESC, pm.user_id ASC
                """
            ),
            {"season_id": season_id, "paddock_id": payload.paddock_id},
        ).mappings().all()

        ranked = compute_dense_ranks_by_key(
            [{"user_id": row["user_id"], "points_total": float(row["points_total"])} for row in rows],
            "points_total",
        )
        standings_payload: list[dict[str, int | float]] = []
        for row in ranked:
            standings_payload.append(
                {
                    "season_id": season_id,
                    "paddock_id": payload.paddock_id,
                    "user_id": row["user_id"],
                    "rank": row["rank"],
                    "points_total": row["points_total"],
                }
            )

        if standings_payload:
            conn.execute(
                text(
                    """
                    INSERT INTO season_standings (season_id, paddock_id, user_id, rank, points_total)
                    VALUES (:season_id, :paddock_id, :user_id, :rank, :points_total)
                    ON CONFLICT (season_id, paddock_id, user_id)
                    DO UPDATE SET rank = EXCLUDED.rank,
                                  points_total = EXCLUDED.points_total
                    """
                ),
                standings_payload,
            )

        stored = conn.execute(
            text(
                """
                SELECT id, season_id, paddock_id, user_id, rank, points_total
                FROM season_standings
                WHERE season_id = :season_id AND paddock_id = :paddock_id
                ORDER BY rank ASC, user_id ASC
                """
            ),
            {"season_id": season_id, "paddock_id": payload.paddock_id},
        ).mappings().all()

    return [SeasonStandingResponse(**row) for row in stored]


@app.get("/standings/season/{season_id}", response_model=list[SeasonStandingResponse])
def get_season_standings(
    season_id: int,
    paddock_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[SeasonStandingResponse]:
    require_paddock_member(current_user.id, paddock_id)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, season_id, paddock_id, user_id, rank, points_total
                FROM season_standings
                WHERE season_id = :season_id AND paddock_id = :paddock_id
                ORDER BY rank ASC, user_id ASC
                """
            ),
            {"season_id": season_id, "paddock_id": paddock_id},
        ).mappings().all()

    return [SeasonStandingResponse(**row) for row in rows]
