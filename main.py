import os

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI
from fastapi.responses import FileResponse


# =========================================================
# CONFIG
# =========================================================

DATABASE_URL = os.environ["DATABASE_URL"].strip()

app = FastAPI(title="RideNow Map")


def get_conn():
    return psycopg.connect(
        DATABASE_URL,
        autocommit=True,
        row_factory=dict_row,
    )


# =========================================================
# PAGE PRINCIPALE
# =========================================================

@app.get("/")
def home():
    return FileResponse("index.html")


# =========================================================
# ALERTES LIVE
# =========================================================

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


# =========================================================
# HISTORIQUE 7 JOURS
# =========================================================

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
                    a.created_at,

                    (
                        SELECT COUNT(*)
                        FROM alert_confirmations ac
                        WHERE ac.alert_id = a.id
                    ) AS confirmations

                FROM alerts a

                WHERE
                    a.created_at >= NOW() - INTERVAL '7 days'

                ORDER BY a.created_at DESC;
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
                "confirmations": alert["confirmations"],
            }
            for alert in alerts
        ]
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "RideNow Map"
    }
