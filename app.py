"""Prosta aplikacja Flask do demonstracji automatyzacji deploymentu."""

import os

import psycopg
from flask import Flask, current_app, jsonify, request
from psycopg.rows import dict_row

DEFAULT_DATABASE_URL = "postgresql://appuser:apppassword@localhost:5432/appdb"


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

    if test_config:
        app.config.update(test_config)

    def connect_db():
        return psycopg.connect(
            current_app.config["DATABASE_URL"],
            row_factory=dict_row,
        )

    @app.get("/")
    def index():
        return jsonify(
            application="Automatyzacja deploymentu",
            status="running",
            endpoints={
                "health": "/health",
                "list_notes": "GET /api/notes",
                "create_note": "POST /api/notes",
            },
        )

    @app.get("/health")
    def health():
        try:
            with connect_db() as conn:
                conn.execute("SELECT 1")
            return jsonify(status="healthy", database="connected"), 200
        except psycopg.Error:
            current_app.logger.exception("Kontrola bazy danych nie powiodła się")
            return jsonify(status="unhealthy", database="unavailable"), 503

    @app.get("/api/notes")
    def list_notes():
        try:
            with connect_db() as conn:
                rows = conn.execute(
                    "SELECT id, content, created_at FROM notes ORDER BY id DESC"
                ).fetchall()
            return jsonify(
                items=[
                    {
                        "id": row["id"],
                        "content": row["content"],
                        "created_at": row["created_at"].isoformat(),
                    }
                    for row in rows
                ]
            )
        except psycopg.Error:
            current_app.logger.exception("Nie udało się pobrać notatek")
            return jsonify(error="Baza danych jest chwilowo niedostępna"), 503

    @app.post("/api/notes")
    def create_note():
        payload = request.get_json(silent=True) or {}
        content = payload.get("content", "")

        if not isinstance(content, str) or not content.strip():
            return jsonify(error="Pole 'content' jest wymagane"), 400
        if len(content.strip()) > 500:
            return jsonify(error="Notatka może mieć maksymalnie 500 znaków"), 400

        try:
            with connect_db() as conn:
                row = conn.execute(
                    "INSERT INTO notes (content) VALUES (%s) "
                    "RETURNING id, content, created_at",
                    (content.strip(),),
                ).fetchone()
            return jsonify(
                note={
                    "id": row["id"],
                    "content": row["content"],
                    "created_at": row["created_at"].isoformat(),
                }
            ), 201
        except psycopg.Error:
            current_app.logger.exception("Nie udało się zapisać notatki")
            return jsonify(error="Baza danych jest chwilowo niedostępna"), 503

    return app


def init_db(database_url=None):
    """Tworzy tabelę aplikacji. Wywoływane przed uruchomieniem serwera."""
    url = database_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    with psycopg.connect(url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id BIGSERIAL PRIMARY KEY,
                content TEXT NOT NULL CHECK (char_length(content) <= 500),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


app = create_app()


if __name__ == "__main__":
    # Tryb developerski. W kontenerze uruchamiany jest Gunicorn.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
