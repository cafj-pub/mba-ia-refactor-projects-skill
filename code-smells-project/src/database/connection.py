import sqlite3

from flask import current_app, g

from src.database.schema import create_schema, seed_if_empty


def get_db():
    """Conexão SQLite com escopo de requisição (uma por app context)."""
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app, seed_admin_password=""):
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = get_db()
        create_schema(conn)
        seed_if_empty(conn, seed_admin_password)
