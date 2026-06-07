import sqlite3
from config import DATABASE_PATH


def get_db_connection():
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    schema_path = DATABASE_PATH.parent / "models" / "schema.sql"

    with open(schema_path, "r", encoding="utf-8") as file:
        conn.executescript(file.read())

    conn.commit()
    conn.close()