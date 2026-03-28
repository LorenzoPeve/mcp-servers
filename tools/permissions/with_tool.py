import os
import json
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(
    auth_token=os.environ["ANTHROPIC_API_KEY"],
)
MODEL = "claude-sonnet-4-6"

DB_CONFIG = {
    "host": "localhost",
    "port": 6666,
    "dbname": "myapp",
    "user": "postgres", # change to readonly_user for example
    "password": "postgres",
}


def execute_query(sql: str) -> str:
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql)

        if cur.description:
            # SELECT — return rows
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchmany(100)
            conn.commit()
            return json.dumps({
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows),
            }, default=str)
        else:
            # INSERT/UPDATE/DELETE — return affected row count
            affected = cur.rowcount
            conn.commit()
            return json.dumps({"affected_rows": affected})

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return json.dumps({"error": f"Database error: {e.pgerror or str(e)}"})
    finally:
        if conn:
            conn.close()


def get_schema_summary() -> str:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(readonly=True)
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
    conn.close()
    return json.dumps(tables, indent=2)


tools = [
    {
        "name": "run_sql_query",
        "description": (
            "Execute a SQL query against the PostgreSQL database."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A single SQL query in PostgreSQL syntax.",
                },
            },
            "required": ["sql"],
        },
    }
]


def process_tool_calls(response):
    results = []
    for block in response.content:
        if block.type == "tool_use":
            sql = block.input["sql"]
            print(f"  [SQL] {sql}")
            result = execute_query(sql)
            print(f"  [Result] {result[:200]}")
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
    return results


def serialize_message(msg):
    """Convert a conversation message to a JSON-serializable dict."""
    role = msg["role"]
    content = msg["content"]
    # Anthropic response content blocks -> list of dicts
    if isinstance(content, list) and content and hasattr(content[0], "type"):
        content = [
            {"type": b.type, "text": b.text} if b.type == "text"
            else {"type": b.type, "id": b.id, "name": b.name, "input": b.input}
            for b in content
        ]
    return {"role": role, "content": content}


def save_conversation(conversation, filepath):
    filepath.write_text(json.dumps(
        [serialize_message(m) for m in conversation],
        indent=2, default=str,
    ))


if __name__ == "__main__":
    schema = get_schema_summary()
    log_path = Path(__file__).parent / "conversation.json"

    system_prompt = f"""
    You are a data analyst. Answer questions by querying a PostgreSQL database.

    Schema:
    {schema}
"""

    conversation = []

    print("Database Q&A (type 'quit' or 'exit' to stop)")
    print("=" * 50)

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        conversation.append({"role": "user", "content": question})

        # Agentic loop: keep going until Claude stops calling tools
        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=system_prompt,
                tools=tools,
                messages=conversation,
            )

            if response.stop_reason == "end_turn":
                answer = next((b.text for b in response.content if b.type == "text"), "")
                conversation.append({"role": "assistant", "content": response.content})
                print(f"\nAssistant: {answer}")
                break

            if response.stop_reason == "tool_use":
                conversation.append({"role": "assistant", "content": response.content})
                tool_results = process_tool_calls(response)
                conversation.append({"role": "user", "content": tool_results})

        save_conversation(conversation, log_path)

    save_conversation(conversation, log_path)
    print(f"Conversation saved to {log_path}")
