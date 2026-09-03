import os

import psycopg
from psycopg.rows import dict_row

from fastapi import FastAPI
from fastapi.responses import FileResponse


DATABASE_URL = os.environ["DATABASE_URL"].strip()

app = FastAPI(title="RideNow Map")


def get_conn():
    return psycopg.connect(
        DATABASE_URL,
        autocommit=True,
        row_factory=dict_row,
    )


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/api/alerts")
def get_alerts():

    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    a.id,
                    a.telegram_message_id,
                    a.category,
                    a.latitude,
                    a.longitude,
                    a.location_name,
                    COALESCE(a.observed_at, a.created_at) AS observed_at,
                    a.created_at,
                    a.updated_at,

                    (
                        SELECT COUNT(*)
                        FROM alert_confirmations ac
                        WHERE ac.alert_id = a.id
                    ) AS confirmations

                FROM alerts a

                WHERE a.active = TRUE

                ORDER BY
                    COALESCE(a.observed_at, a.created_at)
                    DESC;
            """)

            alerts = cur.fetchall()

    return {
        "alerts": [
            {
                "id": a["id"],
                "telegram_message_id": a["telegram_message_id"],
                "category": a["category"],
                "latitude": a["latitude"],
                "longitude": a["longitude"],
                "location_name": a["location_name"] or "Paris",
                "observed_at": a["observed_at"].isoformat(),
                "created_at": a["created_at"].isoformat(),
                "updated_at": a["updated_at"].isoformat(),
                "confirmations": a["confirmations"],
            }
            for a in alerts
        ]
    }


@app.get("/api/history")
def get_history():

    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    a.id,
                    a.category,
                    a.latitude,
                    a.longitude,
                    a.location_name,
                    COALESCE(a.observed_at, a.created_at) AS observed_at,

                    (
                        SELECT COUNT(*)
                        FROM alert_confirmations ac
                        WHERE ac.alert_id = a.id
                    ) AS confirmations

                FROM alerts a

                WHERE
                    COALESCE(
                        a.observed_at,
                        a.created_at
                    )
                    >= NOW() - INTERVAL '7 days'

                ORDER BY
                    COALESCE(
                        a.observed_at,
                        a.created_at
                    )
                    DESC;
            """)

            alerts = cur.fetchall()

    return {
        "alerts": [
            {
                "id": a["id"],
                "category": a["category"],
                "latitude": a["latitude"],
                "longitude": a["longitude"],
                "location_name": a["location_name"] or "Paris",
                "created_at": a["observed_at"].isoformat(),
                "confirmations": a["confirmations"],
            }
            for a in alerts
        ]
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "RideNow Map"
    }
