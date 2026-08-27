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
                    a.created_at,
                    a.updated_at,
                    a.active,
                    (
                        SELECT COUNT(*)
                        FROM alert_confirmations ac
                        WHERE ac.alert_id = a.id
                    ) AS confirmations
                FROM alerts a
                WHERE a.active = TRUE
                ORDER BY a.created_at DESC;
            """)

            alerts = cur.fetchall()

    return {
        "alerts": [
            {
                "id": alert["id"],
                "telegram_message_id": alert["telegram_message_id"],
                "category": alert["category"],
                "latitude": alert["latitude"],
                "longitude": alert["longitude"],
                "location_name": alert["location_name"] or "Paris",
                "created_at": alert["created_at"].isoformat(),
                "updated_at": alert["updated_at"].isoformat(),
                "confirmations": alert["confirmations"],
            }
            for alert in alerts
        ]
    }


@app.get("/api/history")
def get_history():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    category,
                    latitude,
                    longitude,
                    location_name,
                    created_at
                FROM alerts
                WHERE created_at >= NOW() - INTERVAL '7 days'
                ORDER BY created_at DESC;
            """)

            alerts = cur.fetchall()

    return {
        "alerts": [
            {
                "id": alert["id"],
                "category": alert["category"],
                "latitude": alert["latitude"],
                "longitude": alert["longitude"],
                "location_name": alert["location_name"] or "Paris",
                "created_at": alert["created_at"].isoformat(),
            }
            for alert in alerts
        ]
    }
