import mysql.connector
from typing import Any

from utils.config import db_config


def _is_select_query(query: str) -> bool:
    normalized = query.strip()
    if not normalized:
        return False

    # Remove a trailing semicolon for validation, but reject multiple statements
    if normalized.endswith(";"):
        normalized = normalized[:-1].strip()

    if ";" in normalized:
        return False

    return normalized.lower().startswith("select")


def format_query_results(rows: list[dict]) -> str:
    if not rows:
        return "No rows returned."

    columns = list(rows[0].keys())
    widths = {col: max(len(str(col)), max(len(str(row.get(col, ""))) for row in rows)) for col in columns}

    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)
    lines = [header, separator]

    for row in rows:
        lines.append(" | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))

    return "\n".join(lines)


def execute_sql(query: str) -> list[dict[str, Any]]:
    """Execute a safe SELECT query and return rows as list of dictionaries."""
    if not _is_select_query(query):
        raise ValueError("Only single SELECT queries are allowed for execution.")

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except mysql.connector.Error as err:
        raise RuntimeError(f"MySQL execution error: {err}") from err
    except Exception as err:
        raise RuntimeError(f"Query execution error: {err}") from err
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
