# LLM Tools & Database Permissions Demo

This demo shows three things:
1. **Without tools**, an LLM cannot interact with a database at all
2. **With tools**, an LLM can query (and modify!) a database autonomously
3. **Database permissions** are a critical safety layer when giving LLMs write access

## Setup

Start a local Postgres instance and seed it:

```bash
docker run -d \
  --name myapp-postgres \
  -e POSTGRES_DB=myapp \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 6666:5432 \
  postgres:16

```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Demo 1: No Tools

```bash
python basic_no_tools.py
```

The LLM has no way to reach the database. It can only suggest SQL you could run yourself.

> **You:** tell me about how many orders are there?
>
> **Assistant:** I don't have access to any database, system, or data to check order information. Could you clarify what you're referring to?

## Demo 2: With Tools (full access)

```bash
# In with_tool.py, set user to "postgres" (full privileges)
python with_tool.py
```

The LLM gets a `run_sql_query` tool and the database schema in its system prompt. Now it can answer questions by writing and executing SQL on the fly.

> **You:** tell me about how many orders are there?
>
> `[SQL] SELECT COUNT(*) AS total_orders FROM orders;`
>
> **Assistant:** There are a total of **16 orders** in the database.

But here is the danger -- the LLM will also happily execute destructive operations without hesitation:

> **You:** update all the orders before 2026-03-13 to price = 10
>
> `[SQL] UPDATE orders SET price = 10 WHERE ordered_at < '2026-03-13';`
>
> `[Result] {"affected_rows": 16}`
>
> **Assistant:** Done! All 16 orders placed before 2026-03-13 have been set to a price of 10.

The LLM executed an `UPDATE` across the entire table with no confirmation step. This is the core risk of giving an LLM unrestricted tool access.

## Demo 3: With Tools (read-only user)

```bash
# In with_tool.py, set user to "readonly_user"
python with_tool.py
```

Same tool, same code -- but the database user only has `SELECT` privileges. When the LLM tries the same destructive query, Postgres blocks it:

> **You:** update all the orders before 2026-03-13 to price = 10
>
> `[SQL] UPDATE orders SET price = 10 WHERE ordered_at < '2026-03-13';`
>
> `[Result] {"error": "permission denied for table orders"}`
>
> **Assistant:** The current database user does not have permission to modify the orders table.

## Key Takeaway

Tools give LLMs the ability to take actions in the real world. The LLM itself has no concept of "this is dangerous" -- it will run whatever SQL it thinks fulfills the request. **The safety boundary must live outside the LLM**, in this case through database-level permissions (`readonly_user` with only `SELECT` grants).

## Files

| File | Description |
|------|-------------|
| `init.sql` | Creates tables, seeds data, and sets up a read-only Postgres user |
| `basic_no_tools.py` | Plain chat with Claude -- no tools, no database access |
| `with_tool.py` | Chat with a `run_sql_query` tool connected to Postgres |
