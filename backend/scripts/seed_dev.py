from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.db import get_engine


def main() -> None:
    engine = get_engine()
    future_base = datetime.now(UTC) + timedelta(days=30)

    with engine.begin() as conn:
        season = conn.execute(
            text(
                """
                INSERT INTO seasons (year, name, timezone_display)
                VALUES (2026, 'Saison 2026', 'Europe/Paris')
                ON CONFLICT (year) DO UPDATE
                SET name = EXCLUDED.name, timezone_display = EXCLUDED.timezone_display
                RETURNING id
                """
            )
        ).scalar_one()

        gp1 = conn.execute(
            text(
                """
                INSERT INTO grand_prix (season_id, name, country, starts_at_utc, has_sprint, round_number)
                VALUES (:season_id, 'Grand Prix 1', 'France', :starts_at, false, 1)
                ON CONFLICT (season_id, round_number) DO UPDATE
                SET name = EXCLUDED.name,
                    country = EXCLUDED.country,
                    starts_at_utc = EXCLUDED.starts_at_utc,
                    has_sprint = EXCLUDED.has_sprint
                RETURNING id
                """
            ),
            {"season_id": season, "starts_at": future_base},
        ).scalar_one()

        conn.execute(
            text("DELETE FROM sessions WHERE gp_id = :gp_id"),
            {"gp_id": gp1},
        )

        conn.execute(
            text(
                """
                INSERT INTO sessions (gp_id, type, deadline_utc, status)
                VALUES
                    (:gp_id, 'QUALI', :quali_deadline, 'open'),
                    (:gp_id, 'RACE', :race_deadline, 'open')
                """
            ),
            {
                "gp_id": gp1,
                "quali_deadline": future_base + timedelta(days=1),
                "race_deadline": future_base + timedelta(days=2),
            },
        )

        gp2 = conn.execute(
            text(
                """
                INSERT INTO grand_prix (season_id, name, country, starts_at_utc, has_sprint, round_number)
                VALUES (:season_id, 'Grand Prix 2', 'Italie', :starts_at, true, 2)
                ON CONFLICT (season_id, round_number) DO UPDATE
                SET name = EXCLUDED.name,
                    country = EXCLUDED.country,
                    starts_at_utc = EXCLUDED.starts_at_utc,
                    has_sprint = EXCLUDED.has_sprint
                RETURNING id
                """
            ),
            {"season_id": season, "starts_at": future_base + timedelta(days=10)},
        ).scalar_one()

        conn.execute(
            text("DELETE FROM sessions WHERE gp_id = :gp_id"),
            {"gp_id": gp2},
        )

        conn.execute(
            text(
                """
                INSERT INTO sessions (gp_id, type, deadline_utc, status)
                VALUES
                    (:gp_id, 'SPRINT_QUALI', :sq_deadline, 'open'),
                    (:gp_id, 'SPRINT_RACE', :sr_deadline, 'open'),
                    (:gp_id, 'QUALI', :quali_deadline, 'open'),
                    (:gp_id, 'RACE', :race_deadline, 'open')
                """
            ),
            {
                "gp_id": gp2,
                "sq_deadline": future_base + timedelta(days=11),
                "sr_deadline": future_base + timedelta(days=12),
                "quali_deadline": future_base + timedelta(days=13),
                "race_deadline": future_base + timedelta(days=14),
            },
        )


if __name__ == "__main__":
    main()
