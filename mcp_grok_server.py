"""
LeakSnipe multi-database MCP server for Grok (streamable HTTP + stdio).

Exposes all *.db files under the LeakSnipe project (poker_hands.db, coach_memory.db, …).
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

REPO_ROOT = Path(os.environ.get("LEAKSNIPE_ROOT", Path(__file__).resolve().parent)).expanduser().resolve()
# Optional override for a single DB; otherwise all *.db under REPO_ROOT are available.
DEFAULT_DB_ENV = os.environ.get("SQLITE_DB_PATH")

mcp = FastMCP(
    name="LeakSnipe",
    instructions=(
        "LeakSnipe poker hand database (sqlite). Default DB: poker_hands. "
        "Heroes tracked: Gboss101/gboss101 and jdwalka/Johndawalka. "
        "Find hero hands by joining hands with players where is_hero=1 and "
        "name matches (use lower(name) LIKE '%gboss101%' or '%jdwalka%'). "
        "Tools: list_databases, list_tables, describe_table, read_query, "
        "database_overview. Only SELECT/WITH allowed."
    ),
)


def _discover_databases() -> Dict[str, Path]:
    dbs: Dict[str, Path] = {}
    if DEFAULT_DB_ENV:
        p = Path(DEFAULT_DB_ENV).expanduser().resolve()
        if p.exists():
            dbs[p.stem] = p
    for p in sorted(REPO_ROOT.glob("*.db")):
        dbs[p.stem] = p.resolve()
    # Common alternate locations
    for extra in (
        REPO_ROOT / "data",
        Path(os.environ.get("LOCALAPPDATA", "")) / "leaksnipe",
        Path(os.environ.get("APPDATA", "")) / "leaksnipe",
    ):
        if extra.is_dir():
            for p in extra.glob("*.db"):
                dbs.setdefault(p.stem, p.resolve())
    return dbs


def _resolve_db(database: Optional[str] = None) -> Path:
    dbs = _discover_databases()
    if not dbs:
        raise FileNotFoundError(f"No .db files found under {REPO_ROOT}")
    if database:
        key = database.replace(".db", "").strip()
        if key not in dbs:
            raise ValueError(f"Unknown database '{database}'. Available: {list(dbs)}")
        return dbs[key]
    # Prefer poker_hands, else first
    if "poker_hands" in dbs:
        return dbs["poker_hands"]
    return next(iter(dbs.values()))


class SQLiteConnection:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.conn:
            self.conn.close()


def _assert_select(query: str) -> str:
    q = query.strip()
    if q.endswith(";"):
        q = q[:-1].strip()
    in_single = in_double = False
    for ch in q:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ";" and not in_single and not in_double:
            raise ValueError("Multiple SQL statements are not allowed")
    lower = q.lower()
    if not (lower.startswith("select") or lower.startswith("with")):
        raise ValueError("Only SELECT / WITH queries are allowed")
    return q


@mcp.tool()
def list_databases() -> List[Dict[str, Any]]:
    """List all LeakSnipe SQLite databases available on this machine.

    Returns name, path, and size_bytes for each .db file.
    """
    out: List[Dict[str, Any]] = []
    for name, path in _discover_databases().items():
        try:
            size = path.stat().st_size
        except OSError:
            size = None
        out.append({"name": name, "path": str(path), "size_bytes": size})
    return out


@mcp.tool()
def list_tables(database: Optional[str] = None) -> List[str]:
    """List tables in a LeakSnipe database (default: poker_hands).

    Args:
        database: Database name without .db, e.g. 'poker_hands' or 'coach_memory'.
    """
    with SQLiteConnection(_resolve_db(database)) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r["name"] for r in rows]


@mcp.tool()
def describe_table(table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return column schema for a table (name, type, pk, etc.).

    Args:
        table_name: Table to inspect.
        database: Optional DB name (default poker_hands).
    """
    with SQLiteConnection(_resolve_db(database)) as conn:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            [table_name],
        ).fetchone()
        if not exists:
            raise ValueError(f"Table '{table_name}' does not exist")
        safe = table_name.replace('"', "")
        cols = conn.execute(f'PRAGMA table_info("{safe}")').fetchall()
        return [dict(c) for c in cols]


@mcp.tool()
def read_query(
    query: str,
    database: Optional[str] = None,
    params: Optional[List[Any]] = None,
    fetch_all: bool = True,
    row_limit: int = 200,
) -> List[Dict[str, Any]]:
    """Run a read-only SQL SELECT against a LeakSnipe database.

    Args:
        query: SELECT or WITH query only.
        database: Optional DB name (default poker_hands). Use list_databases first.
        params: Optional bound parameters.
        fetch_all: Fetch all rows vs first row.
        row_limit: Max rows (default 200, max 1000).
    """
    query = _assert_select(query)
    params = params or []
    limit = max(1, min(int(row_limit), 1000))
    if "limit" not in query.lower():
        query = f"{query} LIMIT {limit}"

    with SQLiteConnection(_resolve_db(database)) as conn:
        try:
            cur = conn.execute(query, params)
            rows = cur.fetchall() if fetch_all else [cur.fetchone()]
            return [dict(r) for r in rows if r is not None]
        except sqlite3.Error as e:
            raise ValueError(f"SQLite error: {e}") from e


@mcp.tool()
def database_overview(database: Optional[str] = None) -> Dict[str, Any]:
    """Snapshot of one DB (or all if database omitted): tables, hand counts, dates."""
    dbs = _discover_databases()
    targets = {database.replace(".db", ""): dbs[database.replace(".db", "")]} if database else dbs
    if database and database.replace(".db", "") not in dbs:
        raise ValueError(f"Unknown database '{database}'. Available: {list(dbs)}")

    result: Dict[str, Any] = {"repo_root": str(REPO_ROOT), "databases": {}}
    for name, path in targets.items():
        info: Dict[str, Any] = {"path": str(path), "size_bytes": path.stat().st_size}
        with SQLiteConnection(path) as conn:
            tables = [
                r["name"]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
            ]
            info["tables"] = tables
            if "hands" in tables:
                info["hand_count"] = conn.execute("SELECT COUNT(*) AS c FROM hands").fetchone()["c"]
                try:
                    row = conn.execute(
                        "SELECT MIN(date) AS dmin, MAX(date) AS dmax FROM hands"
                    ).fetchone()
                    info["date_min"] = row["dmin"]
                    info["date_max"] = row["dmax"]
                except sqlite3.Error:
                    pass
                try:
                    sites = conn.execute(
                        "SELECT site, COUNT(*) AS c FROM hands GROUP BY site ORDER BY c DESC LIMIT 20"
                    ).fetchall()
                    info["hands_by_site"] = {r["site"]: r["c"] for r in sites}
                except sqlite3.Error:
                    pass
            if "players" in tables:
                try:
                    info["distinct_players"] = conn.execute(
                        "SELECT COUNT(DISTINCT name) AS c FROM players"
                    ).fetchone()["c"]
                except sqlite3.Error:
                    pass
        result["databases"][name] = info
    return result


class _GrokHeaderMiddleware:
    """Make streamable-HTTP compatible with Grok's remote MCP client.

    Grok (and some proxies) send Accept: */* or omit Accept entirely. The MCP
    SDK rejects those with HTTP 406 unless application/json is present.
    This middleware rewrites Accept / Content-Type before the MCP app runs.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = []
            has_accept = False
            has_content_type = False
            method = scope.get("method", "GET").upper()

            for key, value in scope.get("headers", []):
                lk = key.lower()
                if lk == b"accept":
                    has_accept = True
                    # Force both media types the MCP SDK checks for
                    headers.append((b"accept", b"application/json, text/event-stream"))
                    continue
                if lk == b"content-type":
                    has_content_type = True
                    # Normalize to application/json for POST bodies
                    if method in ("POST", "PUT", "PATCH"):
                        headers.append((b"content-type", b"application/json"))
                        continue
                headers.append((key, value))

            if not has_accept:
                headers.append((b"accept", b"application/json, text/event-stream"))
            if method in ("POST", "PUT", "PATCH") and not has_content_type:
                headers.append((b"content-type", b"application/json"))

            # CORS so browser-side probes from grok.com don't fail
            scope = dict(scope)
            scope["headers"] = headers

            async def send_with_cors(message):
                if message["type"] == "http.response.start":
                    extra = [
                        (b"access-control-allow-origin", b"*"),
                        (b"access-control-allow-methods", b"GET, POST, DELETE, OPTIONS"),
                        (
                            b"access-control-allow-headers",
                            b"content-type, accept, mcp-session-id, mcp-protocol-version, authorization",
                        ),
                        (b"access-control-expose-headers", b"mcp-session-id"),
                    ]
                    message = dict(message)
                    message["headers"] = list(message.get("headers", [])) + extra
                await send(message)

            # Handle preflight
            if method == "OPTIONS":
                await send_with_cors(
                    {
                        "type": "http.response.start",
                        "status": 204,
                        "headers": [
                            (b"content-length", b"0"),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": b""})
                return

            await self.app(scope, receive, send_with_cors)
            return

        await self.app(scope, receive, send)


if __name__ == "__main__":
    transport = os.environ.get("LEAKSNIPE_MCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        import uvicorn

        port = int(os.environ.get("LEAKSNIPE_MCP_PORT", "8001"))
        # Build Starlette MCP app, then wrap with Grok-friendly header middleware
        app = mcp.http_app(
            path="/mcp",
            transport="streamable-http",
            json_response=True,
            stateless_http=True,
            # Allow any Host (Cloudflare / Serveo tunnels rewrite Host header)
            host_origin_protection=False,
        )
        app = _GrokHeaderMiddleware(app)
        print(f"LeakSnipe MCP (Grok-compatible headers) on http://127.0.0.1:{port}/mcp")
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
