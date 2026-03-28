import json
import os

import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "6666")),
    "dbname": os.getenv("PG_DATABASE", "myapp"),
    "user": os.getenv("PG_USER", "readonly_user"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
}

mcp = FastMCP("postgres-readonly")


def _get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(readonly=True, autocommit=True)
    return conn


@mcp.tool()
def list_tables() -> str:
    """List all tables in the public schema with their columns and types."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.table_name,
                   json_agg(
                       json_build_object(
                           'column', c.column_name,
                           'type', c.data_type,
                           'nullable', c.is_nullable
                       ) ORDER BY c.ordinal_position
                   ) AS columns
            FROM information_schema.tables t
            JOIN information_schema.columns c
                ON t.table_name = c.table_name AND t.table_schema = c.table_schema
            WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
            GROUP BY t.table_name ORDER BY t.table_name;
        """)
        tables = {name: cols for name, cols in cur.fetchall()}
        return json.dumps(tables, indent=2)
    finally:
        conn.close()


@mcp.tool()
def read_query(sql: str) -> str:
    """Execute a read-only SQL query against the PostgreSQL database.

    Only SELECT queries are allowed. The connection is read-only so any
    INSERT, UPDATE, DELETE, or DDL statements will be rejected by the database.

    Args:
        sql: A SELECT query in PostgreSQL syntax.
    """
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)

        if cur.description is None:
            return json.dumps({"error": "Query did not return results. Only SELECT queries are supported."})

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchmany(100)
        return json.dumps(
            {
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows),
            },
            default=str,
        )
    except psycopg2.Error as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run()
