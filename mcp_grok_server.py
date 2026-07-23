"""
LeakSnipe multi-database MCP server for Grok (streamable HTTP + stdio).

Exposes all *.db files under the LeakSnipe project (poker_hands.db, coach_memory.db, …).
"""
from __future__ import annotations

import os
import sys
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

REPO_ROOT = Path(os.environ.get("LEAKSNIPE_ROOT", Path(__file__).resolve().parent)).expanduser().resolve()
# Optional override for a single DB; otherwise all *.db under REPO_ROOT are available.
DEFAULT_DB_ENV = os.environ.get("SQLITE_DB_PATH")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.append(str(REPO_ROOT / "sidecar"))

try:
    from models import HandDatabase, Hand
    from config import load_settings
    from utils import resolve_hand_hero_name
    from coach_memory import CoachMemory
except Exception as e:
    sys.stderr.write(f"[LeakSnipe-Grok] Imports failed: {e}\n")
    sys.stderr.flush()

mcp = FastMCP(
    name="LeakSnipe",
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


def serialize_hand(hand: Hand, settings: dict) -> dict:
    hero_name = resolve_hand_hero_name(
        settings,
        hand.site,
        players=hand.players,
        raw_text=hand.raw_text,
        hero_player=getattr(hand, "hero_player", ""),
    )
    date_str = hand.date.isoformat() if hand.date else None

    return {
        "hand_id": hand.hand_id,
        "site": hand.site,
        "date": date_str,
        "game_type": hand.game_type,
        "is_tournament": hand.is_tournament,
        "table_name": hand.table_name,
        "hero_cards": hand.hero_cards,
        "board_cards": hand.board_cards,
        "pot": hand.pot,
        "rake": hand.rake,
        "hero_won": hand.hero_won,
        "hero_position": hand.hero_position,
        "hero_name": hero_name,
        "players": [
            {
                "seat": seat,
                "name": p["name"],
                "stack": p["stack"],
                "is_hero": p.get("is_hero", False)
            }
            for seat, p in hand.players.items()
        ],
        "streets": [
            {
                "name": street.get("name", ""),
                "cards": street.get("cards", []),
                "actions": [
                    {
                        "player": act.get("player", ""),
                        "action": act.get("action", ""),
                        "amount": act.get("amount", 0.0)
                    }
                    for act in street.get("actions", [])
                ]
            }
            for street in getattr(hand, "streets", [])
        ],
        "winners": [
            {
                "name": w["name"],
                "amount": w["amount"]
            }
            for w in getattr(hand, "winners", [])
        ],
        "raw_text": hand.raw_text
    }


def _safe_decode(b):
    if not b:
        return ""
    for encoding in ['utf-8', 'cp1252', 'cp850']:
        try:
            return b.decode(encoding)
        except UnicodeDecodeError:
            continue
    return b.decode('utf-8', errors='replace')


def _exec_cmd(cmd_list, cwd=None):
    import subprocess
    cmd_str = " ".join(cmd_list)
    res = subprocess.run(
        cmd_str,
        cwd=cwd,
        shell=True,
        capture_output=True,
        timeout=30
    )
    return {
        "stdout": _safe_decode(res.stdout),
        "stderr": _safe_decode(res.stderr),
        "exit_code": res.returncode
    }


def build_cards_sql(cards: str) -> tuple[str, list]:
    c = cards.strip().lower()
    if not c or len(c) < 2:
        return "", []
    c1, c2 = c[0].upper(), c[1].upper()
    if c1 == c2:
        return "hero_cards LIKE ?", [f"{c1}% {c2}%"]
    p1 = f"{c1}% {c2}%"
    p2 = f"{c2}% {c1}%"
    if len(c) >= 3 and c[2] == 's':
        return "( (hero_cards LIKE ? OR hero_cards LIKE ?) AND SUBSTR(hero_cards, 2, 1) = SUBSTR(hero_cards, 5, 1) )", [p1, p2]
    elif len(c) >= 3 and c[2] == 'o':
        return "( (hero_cards LIKE ? OR hero_cards LIKE ?) AND SUBSTR(hero_cards, 2, 1) != SUBSTR(hero_cards, 5, 1) )", [p1, p2]
    else:
        return "(hero_cards LIKE ? OR hero_cards LIKE ?)", [p1, p2]


def parse_natural_language_query(query: str) -> tuple[str, list, int]:
    import re
    query_lower = query.lower()
    where_clauses = []
    params = []

    pos_map = {
        "utg": "UTG", "mp": "MP", "hj": "HJ", "co": "CO", "cutoff": "CO",
        "btn": "BTN", "button": "BTN", "sb": "SB", "small blind": "SB",
        "bb": "BB", "big blind": "BB"
    }
    for key, val in pos_map.items():
        if f"from {key}" in query_lower or f"at {key}" in query_lower or f"in {key}" in query_lower or (f" {key} " in f" {query_lower} "):
            where_clauses.append("hero_position = ?")
            params.append(val)
            break

    if "won" in query_lower or "winning" in query_lower or "profit" in query_lower:
        where_clauses.append("hero_won > 0")
    elif "lost" in query_lower or "losing" in query_lower or "loss" in query_lower:
        where_clauses.append("hero_won < 0")

    if "3-bet" in query_lower or "3bet" in query_lower:
        where_clauses.append("(raw_text LIKE '%3-bet%' OR raw_text LIKE '%3bet%')")
    elif "4-bet" in query_lower or "4bet" in query_lower:
        where_clauses.append("(raw_text LIKE '%4-bet%' OR raw_text LIKE '%4bet%')")
    elif "all-in" in query_lower or "allin" in query_lower or "all in" in query_lower:
        where_clauses.append("(raw_text LIKE '%all-in%' OR raw_text LIKE '%all in%')")

    card_pattern = re.compile(r'\b([2-9tjqka]{2})([so]?)\b', re.IGNORECASE)
    card_match = card_pattern.search(query_lower)
    if card_match:
        cards_input = card_match.group(1).upper()
        suited_offsuited = card_match.group(2).lower()
        c1, c2 = cards_input[0], cards_input[1]
        if c1 == c2:
            where_clauses.append("hero_cards LIKE ?")
            params.append(f"{c1}% {c2}%")
        else:
            p1 = f"{c1}% {c2}%"
            p2 = f"{c2}% {c1}%"
            if suited_offsuited == 's':
                where_clauses.append("( (hero_cards LIKE ? OR hero_cards LIKE ?) AND SUBSTR(hero_cards, 2, 1) = SUBSTR(hero_cards, 5, 1) )")
                params.extend([p1, p2])
            elif suited_offsuited == 'o':
                where_clauses.append("( (hero_cards LIKE ? OR hero_cards LIKE ?) AND SUBSTR(hero_cards, 2, 1) != SUBSTR(hero_cards, 5, 1) )")
                params.extend([p1, p2])
            else:
                where_clauses.append("(hero_cards LIKE ? OR hero_cards LIKE ?)")
                params.extend([p1, p2])

    if "coinpoker" in query_lower or "coin poker" in query_lower:
        where_clauses.append("site = ?")
        params.append("CoinPoker")
    elif "acr" in query_lower or "wpn" in query_lower or "americas" in query_lower:
        where_clauses.append("site = ?")
        params.append("BetACR")

    limit = 10
    limit_match = re.search(r'\blimit\s+(\d+)\b', query_lower)
    if not limit_match:
        limit_match = re.search(r'\blast\s+(\d+)\b', query_lower)
    if limit_match:
        limit = int(limit_match.group(1))

    if not where_clauses:
        where_str = " WHERE (raw_text LIKE ? OR hand_id LIKE ? OR table_name LIKE ?)"
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
    else:
        where_str = " WHERE " + " AND ".join(where_clauses)
    return where_str, params, limit


def session_id_cte(gap_minutes: int = 30) -> str:
    """A CTE that tags every row in `hands` with a computed session_id — a per-site
    sit-down grouping using the same gap-based heuristic as get_sessions_winrate below.
    Must run over the FULL, unfiltered hand history per site (LAG needs the true previous
    hand's date) — any caller-supplied filter has to be applied outside this CTE
    (`SELECT * FROM session_hands WHERE ...`), never folded into it, or the gap
    calculation silently breaks (windowing over an already-filtered subset collapses
    everything into session_id=1). Computed at query time, not persisted.

    Split into two CTE steps (gaps, then session_hands) rather than nesting LAG()
    directly inside SUM()'s argument — SQLite rejects a window function used as an
    input expression to another window function in the same SELECT ("misuse of window
    function LAG()"), verified against sqlite3 3.45.1 locally. get_sessions_winrate
    below has this same nested pattern and hits the same error — out of scope here,
    but worth fixing separately."""
    gm = min(max(int(gap_minutes or 30), 1), 1440)
    return f"""
        WITH gaps AS (
            SELECT h.*,
                LAG(h.date) OVER (PARTITION BY h.site ORDER BY h.date) AS prev_date
            FROM hands h
        ),
        session_hands AS (
            SELECT *,
                SUM(CASE WHEN
                    prev_date IS NULL OR (julianday(date) - julianday(prev_date)) * 24 * 60 > {gm}
                THEN 1 ELSE 0 END) OVER (PARTITION BY site ORDER BY date) AS session_id
            FROM gaps
        )
    """


def query_and_serialize_hands(db, settings, sql, params):
    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            rows = c.execute(sql, params).fetchall()
            if not rows:
                return []
            hand_ids = [row["hand_id"] for row in rows]
            session_ids = {
                row["hand_id"]: row["session_id"]
                for row in rows
                if "session_id" in row.keys()
            }
            players_by_hand, actions_by_hand, winners_by_hand, tags_by_hand = (
                db._load_related_for_ids(c, hand_ids)
            )
            hands = [
                db._hydrate_hand(
                    row, players_by_hand, actions_by_hand, winners_by_hand, tags_by_hand
                )
                for row in rows
            ]
            serialized = [serialize_hand(h, settings) for h in hands]
            if session_ids:
                for s in serialized:
                    s["session_id"] = session_ids.get(s.get("hand_id"))
            return serialized
        finally:
            conn.close()


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
                try:
                    units = conn.execute(
                        """
                        SELECT is_tournament, site, COUNT(*) AS hands,
                               ROUND(SUM(hero_won), 2) AS net
                        FROM hands GROUP BY is_tournament, site
                        """
                    ).fetchall()
                    info["unit_split"] = [dict(r) for r in units]
                    info["unit_note"] = (
                        "is_tournament=0 net is USD; is_tournament=1 net is tournament chips — never mix"
                    )
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


@mcp.tool()
def list_full_schemas() -> Dict[str, Any]:
    """List every available database, table, and column for deep MCP coaching.

    Includes unit rules: cash hands use dollars; tournament hands use chips.
    Heroes: Gboss101 / jdwalka (JohnDaWalka) aliases.
    """
    out: Dict[str, Any] = {
        "heroes": {
            "Gboss101": ["Gboss101", "GBOSS101", "gboss101"],
            "jdwalka": ["jdwalka", "JohnDaWalka", "Johndawalka"],
        },
        "units": {
            "cash": "hero_won/pot are USD when hands.is_tournament = 0",
            "tournament": "hero_won/pot are chips when hands.is_tournament = 1",
        },
        "databases": {},
    }
    for name, path in _discover_databases().items():
        tables: Dict[str, Any] = {}
        with SQLiteConnection(path) as conn:
            for (tname,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "AND name NOT LIKE '%backup%' ORDER BY name"
            ):
                cols = [
                    {"name": r["name"], "type": r["type"], "pk": r["pk"]}
                    for r in conn.execute(f'PRAGMA table_info("{tname}")')
                ]
                try:
                    n = conn.execute(f'SELECT COUNT(*) AS c FROM "{tname}"').fetchone()["c"]
                except sqlite3.Error:
                    n = None
                tables[tname] = {"columns": cols, "row_count": n}
        out["databases"][name] = {"path": str(path), "tables": tables}
    return out


@mcp.tool()
def hero_overview(hero: Optional[str] = None) -> Dict[str, Any]:
    """Hero coaching snapshot with cash $ and tournament chips SEPARATED by site.

    Args:
        hero: 'gboss101', 'jdwalka', or empty for all tracked heroes.
    """
    hero_key = (hero or "").strip().lower()
    clauses = ["p.is_hero = 1"]
    params: List[Any] = []
    if "gboss" in hero_key:
        clauses.append("lower(p.name) LIKE '%gboss101%'")
    elif "jdwalk" in hero_key or "johnda" in hero_key:
        clauses.append(
            "(lower(p.name) LIKE '%jdwalka%' OR lower(p.name) LIKE '%johndawalka%')"
        )
    elif hero_key:
        clauses.append("lower(p.name) = lower(?)")
        params.append(hero_key)

    where = " AND ".join(clauses)
    sql = f"""
        SELECT
          CASE WHEN h.is_tournament = 1 THEN 'tournament_chips' ELSE 'cash_usd' END AS unit,
          h.site,
          COUNT(*) AS hands,
          ROUND(SUM(h.hero_won), 2) AS net,
          ROUND(AVG(h.hero_won), 2) AS avg_result,
          MIN(h.date) AS first_hand,
          MAX(h.date) AS last_hand
        FROM hands h
        JOIN players p ON p.hand_id = h.hand_id AND {where}
        GROUP BY unit, h.site
        ORDER BY unit, hands DESC
    """
    with SQLiteConnection(_resolve_db("poker_hands")) as conn:
        rows = [dict(r) for r in conn.execute(sql, params)]
    return {
        "hero": hero_key or "all",
        "note": "Never add cash_usd net to tournament_chips net",
        "breakdown": rows,
    }


@mcp.tool()
def list_ai_analyses(limit: int = 20, has_mistakes: bool = False) -> List[Dict[str, Any]]:
    """List stored AI coach analyses from ai_analysis for leak review."""
    limit = max(1, min(int(limit), 100))
    sql = (
        "SELECT hand_id, llm_provider, play_style, mistakes_found, tags, summary, "
        "ev_estimate, analyzed_at FROM ai_analysis"
    )
    if has_mistakes:
        sql += " WHERE COALESCE(mistakes_found, 0) > 0"
    sql += " ORDER BY analyzed_at DESC LIMIT ?"
    with SQLiteConnection(_resolve_db("poker_hands")) as conn:
        return [dict(r) for r in conn.execute(sql, [limit])]


@mcp.tool()
def list_coach_memory(hero: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Read coach_memory dialogue history for cross-session coaching context."""
    limit = max(1, min(int(limit), 100))
    sql = (
        "SELECT id, hero, kind, user_text, assistant_text, provider, created_at "
        "FROM coach_memory"
    )
    params: List[Any] = []
    if hero:
        sql += " WHERE lower(hero) LIKE lower(?)"
        params.append(f"%{hero}%")
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with SQLiteConnection(_resolve_db("coach_memory")) as conn:
        return [dict(r) for r in conn.execute(sql, params)]


@mcp.tool()
def write_coach_memory(
    hero: str,
    assistant_text: str,
    provider: str,
    kind: str = "note",
    user_text: str = "",
) -> Dict[str, Any]:
    """Persist a coaching note or dialogue turn to coach_memory (creates the DB/table on
    first use). Use this to save coaching observations taken during this session.

    Args:
        hero: Hero this note is about (e.g. 'jdwalka', 'Gboss101').
        assistant_text: The coaching note / observation to persist.
        provider: Which agent wrote this: 'claude' or 'grok'.
        kind: Type of entry, e.g. 'note' or 'turn' (default 'note').
        user_text: The user-side text (question, hand context, etc.), for kind='turn'.
    """
    hero = (hero or "").strip()
    assistant_text = (assistant_text or "").strip()
    provider = (provider or "").strip()
    if not hero:
        raise ValueError("hero is required")
    if not assistant_text:
        raise ValueError("assistant_text is required")
    if not provider:
        raise ValueError("provider is required (e.g. 'claude' or 'grok')")
    mem = CoachMemory()
    if kind == "turn":
        mem.add_turn(hero, user_text, assistant_text, provider=provider)
    else:
        mem.add_note(hero, assistant_text, kind=kind, provider=provider)
    return {"success": True, "hero": hero, "kind": kind, "provider": provider}


@mcp.tool()
def get_live_table_read(
    site: Optional[str] = None,
    table: Optional[str] = None,
    database: Optional[str] = None,
) -> Dict[str, Any]:
    """Live read on the current table: seats/last-known stacks from the most recently
    imported hand, plus career VPIP/PFR/AF/WTSD/3-bet for every opponent currently seated.
    Note: hand histories only land after a hand completes, so this reflects the latest
    completed hand, not a mid-hand snapshot.

    Args:
        site: Optional site filter (e.g. 'BetACR', 'CoinPoker').
        table: Optional table name/tournament_id filter.
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))

    heroes = set()
    for aliases in (settings.get("hero_names") or {}).values():
        for alias in str(aliases).split(","):
            alias = alias.strip()
            if alias:
                heroes.add(alias)

    hands = db.get_hands_page(50, 0)
    hand = None
    site_filter = (site or "").strip()
    table_filter = (table or "").strip().lower()
    if table_filter == "coinpoker":
        table_filter = ""
    for h in hands:
        if site_filter and h.site.lower() != site_filter.lower():
            continue
        if table_filter:
            h_table = (h.table_name or "").strip().lower()
            h_tid = str(h.tournament_id or "").strip().lower()
            if table_filter not in h_table and h_table not in table_filter and table_filter != h_tid:
                continue
        hand = h
        break
    if hand is None and site_filter:
        for h in hands:
            if h.site.lower() == site_filter.lower():
                hand = h
                break
    if hand is None and hands:
        hand = hands[0]

    if not hand:
        return {
            "ok": True, "hand_id": None, "site": None, "max_seats": 6,
            "seat_map": {}, "opponents": [], "table_name": None, "opponents_read": [],
        }

    seat_map = {}
    opponents = []
    for seat, info in sorted(hand.players.items()):
        name = str(info.get("name") or "").strip()
        is_hero = bool(info.get("is_hero")) or name in heroes
        seat_map[str(seat)] = {"name": name, "is_hero": is_hero, "stack": info.get("stack")}
        if name and not is_hero:
            opponents.append(name)

    opponents_read = []
    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            for name in opponents:
                row = conn.execute(
                    "SELECT name, site, hands, vpip, pfr, af, fold_cbet, wtsd, three_bet, updated_at "
                    "FROM player_types WHERE lower(name) = lower(?)",
                    (name,),
                ).fetchone()
                opponents_read.append({**dict(row), "found": True} if row else {"name": name, "found": False})
        finally:
            conn.close()

    return {
        "ok": True,
        "hand_id": hand.hand_id,
        "site": hand.site,
        "max_seats": hand.max_seats or 6,
        "seat_map": seat_map,
        "opponents": opponents,
        "table_name": hand.table_name,
        "opponents_read": opponents_read,
    }


@mcp.tool()
def get_hand_by_number(
    hand_number: str,
    site: Optional[str] = None,
    tournament_id: Optional[str] = None,
    gap_minutes: int = 30,
    database: Optional[str] = None
) -> Dict[str, Any]:
    """Get exactly one hand by its hand_number (reliable single-hand lookup — prefer this
    over search_hands when you know the hand number, not the internal hand_id).

    Args:
        hand_number: The hand_number to look up, e.g. '96'.
        site: Optional site filter to disambiguate (e.g. 'BetACR', 'CoinPoker').
        tournament_id: Optional tournament_id filter to disambiguate.
        gap_minutes: Session-boundary gap in minutes for the computed session_id (default 30).
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))
    lookup = db.get_hand_by_number(hand_number, site=site, tournament_id=tournament_id)
    if lookup["matches"] == 1:
        detail = serialize_hand(lookup["hand"], settings)
        with db.lock:
            conn = db._connect()
            try:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    f"{session_id_cte(gap_minutes)} SELECT session_id FROM session_hands WHERE hand_id = ?",
                    [lookup["hand"].hand_id],
                ).fetchone()
                detail["session_id"] = row["session_id"] if row else None
            finally:
                conn.close()
        return {"success": True, "found": True, "hand": detail}
    if lookup["matches"] == 0:
        site_note = f" on site {site}" if site else ""
        return {"success": False, "found": False, "error": f"No hand found with hand_number {hand_number}{site_note}"}
    return {
        "success": False,
        "found": False,
        "error": f"{lookup['matches']} hands match hand_number {hand_number} — disambiguate with site and/or tournament_id",
        "candidates": lookup["candidates"],
    }


@mcp.tool()
def get_recent_hands(
    limit: int = 10,
    since: Optional[str] = None,
    gap_minutes: int = 30,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns the most recent hands played by the user.

    Args:
        limit: Max hands to return (default 10).
        since: ISO timestamp YYYY-MM-DD to get hands after.
        gap_minutes: Session-boundary gap in minutes for the computed session_id (default 30).
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))
    where_clauses = []
    sql_params = []
    if since:
        where_clauses.append("date >= ?")
        sql_params.append(since)
    where_str = ""
    if where_clauses:
        where_str = " WHERE " + " AND ".join(where_clauses)
    sql = f"{session_id_cte(gap_minutes)} SELECT * FROM session_hands{where_str} ORDER BY date DESC LIMIT ?"
    return query_and_serialize_hands(db, settings, sql, sql_params + [limit])


@mcp.tool()
def get_hands_by_cards(
    cards: str,
    limit: int = 10,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns hands containing specific hole cards (e.g. 'QQ', 'AKs', '76s').

    Args:
        cards: Card string like 'QQ', 'AK', '76s'.
        limit: Max hands to return (default 10).
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))
    cards_sql, cards_params = build_cards_sql(cards)
    if not cards_sql:
        raise ValueError("Invalid cards specified")
    sql = f"SELECT * FROM hands WHERE {cards_sql} ORDER BY date DESC LIMIT ?"
    return query_and_serialize_hands(db, settings, sql, cards_params + [limit])


@mcp.tool()
def get_biggest_winning_hands(
    limit: int = 10,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns the biggest winning hands by profit.

    Args:
        limit: Max hands to return (default 10).
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))
    sql = "SELECT * FROM hands WHERE hero_won > 0 ORDER BY hero_won DESC LIMIT ?"
    return query_and_serialize_hands(db, settings, sql, [limit])


@mcp.tool()
def get_winrate_by_position(
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns winrate statistics broken down by position.

    Args:
        database: Optional database name (default: poker_hands).
    """
    db = HandDatabase(str(_resolve_db(database)))
    sql = """
        SELECT
            hero_position,
            COUNT(*) as hands_played,
            SUM(hero_won) as net_profit,
            SUM(CASE WHEN hero_won > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM hands
        WHERE hero_position IS NOT NULL AND hero_position != '?'
        GROUP BY hero_position
        ORDER BY net_profit DESC
    """
    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


@mcp.tool()
def get_hands_by_position(
    position: str,
    limit: int = 10,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns hands played from a specific position.

    Args:
        position: Position like 'UTG', 'MP', 'HJ', 'CO', 'BTN', 'SB', 'BB'.
        limit: Max hands to return (default 10).
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))
    sql = "SELECT * FROM hands WHERE UPPER(hero_position) = ? ORDER BY date DESC LIMIT ?"
    return query_and_serialize_hands(db, settings, sql, [position.upper(), limit])


@mcp.tool()
def search_hands(
    query: str,
    limit: Optional[int] = None,
    offset: int = 0,
    gap_minutes: int = 30,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Natural language search across hands (e.g. 'my last 3-bet pot from cutoff').
    Note: for a specific hand_number, prefer get_hand_by_number, which guarantees a
    single unambiguous result.

    Args:
        query: Natural language search query.
        limit: Optional limit to override query limit.
        offset: Pagination offset.
        gap_minutes: Session-boundary gap in minutes for the computed session_id (default 30).
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))
    where_str, sql_params, parsed_limit = parse_natural_language_query(query)
    lim = limit if limit is not None else parsed_limit
    sql = f"{session_id_cte(gap_minutes)} SELECT * FROM session_hands{where_str} ORDER BY date DESC LIMIT ? OFFSET ?"
    return query_and_serialize_hands(db, settings, sql, sql_params + [lim, offset])


@mcp.tool()
def get_sessions_winrate(
    site: Optional[str] = None,
    gap_minutes: int = 30,
    limit: int = 10,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns winrate statistics for playing sessions.

    Args:
        site: Filter by poker site (e.g. 'CoinPoker', 'BetACR').
        gap_minutes: Minutes of inactivity to define session boundary (default 30).
        limit: Max sessions to return (default 10).
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))
    where_clauses = []
    params = []
    if site:
        where_clauses.append("h.site = ?")
        params.append(site)
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    sql = f"""
        WITH session_hands AS (
            SELECT
                h.*,
                SUM(CASE WHEN
                    julianday(h.date) - julianday(LAG(h.date) OVER (ORDER BY h.date)) * 24 * 60 > ?
                    OR LAG(h.date) OVER (ORDER BY h.date) IS NULL
                THEN 1 ELSE 0 END) OVER (ORDER BY h.date) AS session_id
            FROM hands h
            WHERE {where_clause}
        ),
        session_stats AS (
            SELECT
                session_id,
                COUNT(*) AS hands,
                SUM(hero_won) AS net_result,
                AVG(hero_won) AS avg_result,
                MIN(date) AS session_start,
                MAX(date) AS session_end
            FROM session_hands
            GROUP BY session_id
        )
        SELECT
            session_id,
            hands,
            ROUND(net_result, 2) AS net_result,
            ROUND(avg_result, 2) AS avg_result,
            session_start,
            session_end
        FROM session_stats
        ORDER BY net_result DESC
        LIMIT ?
    """
    params.extend([gap_minutes, limit])
    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


# ===== NEW MCP QUERIES FOR LEAK SNIPE ENHANCEMENT =====

@mcp.tool()
def get_hero_vpip_pfr_by_position(
    hero_name: str,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get hero's VPIP and PFR percentages by position.

    Args:
        hero_name: Hero player name to analyze (e.g. 'Gboss101', 'jdwalka').
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))

    sql = """
    WITH hero_hands AS (
        SELECT h.hand_id, h.hero_position
        FROM hands h
        JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
        WHERE p.name = ?
    ),
    hero_actions AS (
        SELECT hh.hand_id, hh.hero_position,
               CASE WHEN EXISTS (SELECT 1 FROM actions a WHERE a.hand_id = hh.hand_id AND a.street = 'preflop' AND a.player = ? AND a.action IN ('call','bet','raise')) THEN 1 ELSE 0 END AS vpip,
               CASE WHEN EXISTS (SELECT 1 FROM actions a WHERE a.hand_id = hh.hand_id AND a.street = 'preflop' AND a.player = ? AND a.action IN ('bet','raise')) THEN 1 ELSE 0 END AS pfr
        FROM hero_hands hh
    )
    SELECT ha.hero_position AS position,
           ROUND(AVG(ha.vpip) * 100, 2) AS vpip_percent,
           ROUND(AVG(ha.pfr) * 100, 2) AS pfr_percent,
           COUNT(*) AS hands
    FROM hero_actions ha
    GROUP BY ha.hero_position
    ORDER BY
        CASE ha.hero_position
            WHEN 'UTG' THEN 1
            WHEN 'UTG+1' THEN 2
            WHEN 'UTG+2' THEN 3
            WHEN 'MP' THEN 4
            WHEN 'HJ' THEN 5
            WHEN 'CO' THEN 6
            WHEN 'BTN' THEN 7
            WHEN 'SB' THEN 8
            WHEN 'BB' THEN 9
            ELSE 10
        END
    """

    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (hero_name, hero_name, hero_name)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


@mcp.tool()
def get_hero_avg_3bet_size_by_position(
    hero_name: str,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get hero's average 3-bet size by position.

    Args:
        hero_name: Hero player name to analyze (e.g. 'Gboss101', 'jdwalka').
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))

    sql = """
    WITH hero_hands AS (
        SELECT h.hand_id, h.hero_position
        FROM hands h
        JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
        WHERE p.name = ?
    ),
    preflop_actions AS (
        SELECT a.hand_id, a.player, a.action, a.amount,
               ROW_NUMBER() OVER (PARTITION BY a.hand_id ORDER BY a.sequence) AS action_order
        FROM actions a
        WHERE a.street = 'preflop'
    ),
    three_bets AS (
        SELECT pa.hand_id, pa.amount
        FROM preflop_actions pa
        WHERE pa.action = 'raise'
          AND (
                SELECT COUNT(*)
                FROM preflop_actions pa2
                WHERE pa2.hand_id = pa.hand_id
                  AND pa2.action IN ('bet','raise')
                  AND pa2.action_order < pa.action_order
              ) >= 2
    )
    SELECT hh.hero_position AS position,
           ROUND(AVG(tb.amount), 2) AS avg_3bet_size,
           COUNT(*) AS count
    FROM three_bets tb
    JOIN hero_hands hh ON tb.hand_id = hh.hand_id
    WHERE tb.player = ?
    GROUP BY hh.hero_position
    ORDER BY
        CASE hh.hero_position
            WHEN 'UTG' THEN 1
            WHEN 'UTG+1' THEN 2
            WHEN 'UTG+2' THEN 3
            WHEN 'MP' THEN 4
            WHEN 'HJ' THEN 5
            WHEN 'CO' THEN 6
            WHEN 'BTN' THEN 7
            WHEN 'SB' THEN 8
            WHEN 'BB' THEN 9
            ELSE 10
        END
    """

    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (hero_name, hero_name)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


@mcp.tool()
def get_opponent_avg_vpip_by_position(
    hero_name: str,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get average VPIP of opponents by position.

    Args:
        hero_name: Hero player name to exclude (e.g. 'Gboss101', 'jdwalka').
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))

    sql = """
    SELECT ppf.position,
           ROUND(AVG(ppf.vpip) * 100, 2) AS avg_vpip_percent,
           COUNT(*) AS hands
    FROM player_position_facts ppf
    WHERE ppf.player != ?
    GROUP BY ppf.position
    ORDER BY
        CASE ppf.position
            WHEN 'UTG' THEN 1
            WHEN 'UTG+1' THEN 2
            WHEN 'UTG+2' THEN 3
            WHEN 'MP' THEN 4
            WHEN 'HJ' THEN 5
            WHEN 'CO' THEN 6
            WHEN 'BTN' THEN 7
            WHEN 'SB' THEN 8
            WHEN 'BB' THEN 9
            ELSE 10
        END
    """

    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (hero_name,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


@mcp.tool()
def get_hero_winrate_tournaments_vs_cash(
    hero_name: str,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get hero's win rate in tournaments vs cash games (bb/100).

    Args:
        hero_name: Hero player name to analyze (e.g. 'Gboss101', 'jdwalka').
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))

    sql = """
    WITH hand_results AS (
        SELECT h.hand_id,
               h.is_tournament,
               CASE WHEN h.is_tournament = 1 THEN 'tournament' ELSE 'cash' END AS game_type,
               (SELECT p.stack FROM players p WHERE p.hand_id = h.hand_id AND p.is_hero = 1) AS hero_start_stack,
               h.hero_won
        FROM hands h
        JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
        WHERE p.name = ?
    ),
    bb_calculated AS (
        SELECT hr.game_type,
               SUM(hr.hero_won) / NULLIF(SUM(hr.hero_start_stack), 0) * 100 AS bb_per_hand
        FROM hand_results hr
        GROUP BY hr.game_type
    )
    SELECT bc.game_type,
           ROUND(bc.bb_per_hand * 100, 2) AS bb_per_100_hands
    FROM bb_calculated bc
    """

    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (hero_name,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


@mcp.tool()
def get_hero_avg_roi_tournaments(
    hero_name: str,
    database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get hero's average ROI in tournaments.

    Args:
        hero_name: Hero player name to analyze (e.g. 'Gboss101', 'jdwalka').
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))

    sql = """
    WITH tourney_hands AS (
        SELECT h.hand_id,
               h.tournament_id,
               CAST(REPLACE(REPLACE(h.buy_in, '$', ''), ',', '') AS REAL) AS buy_in_amount,
               h.hero_won
        FROM hands h
        JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
        WHERE p.name = ?
          AND h.is_tournament = 1
          AND h.buy_in IS NOT NULL
    ),
    agg AS (
        SELECT th.tournament_id,
               SUM(th.hero_won) AS total_won,
               SUM(th.buy_in_amount) AS total_buy_in
        FROM tourney_hands th
        GROUP BY th.tournament_id
    )
    SELECT ROUND(AVG((a.total_won - a.total_buy_in) / NULLIF(a.total_buy_in, 0) * 100), 2) AS average_roi_percent
    FROM agg a
    """

    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (hero_name,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


@mcp.tool()
def get_hero_leak_report(
    hero_name: str,
    database: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a comprehensive leak report for a hero player.

    Args:
        hero_name: Hero player name to analyze (e.g. 'Gboss101', 'jdwalka').
        database: Optional database name (default: poker_hands).
    """
    settings = load_settings()
    db = HandDatabase(str(_resolve_db(database)))

    # Get overall stats
    overall_sql = """
    SELECT
        COUNT(*) AS total_hands,
        SUM(CASE WHEN hero_won > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS win_rate_percent,
        AVG(hero_won) AS avg_bb_per_hand,
        SUM(hero_won) AS total_bb_won
    FROM hands h
    JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
    WHERE p.name = ?
    """

    # Get VPIP/PFR by position
    vpip_pfr_sql = """
    WITH hero_hands AS (
        SELECT h.hand_id, h.hero_position
        FROM hands h
        JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
        WHERE p.name = ?
    ),
    hero_actions AS (
        SELECT hh.hand_id, hh.hero_position,
               CASE WHEN EXISTS (SELECT 1 FROM actions a WHERE a.hand_id = hh.hand_id AND a.street = 'preflop' AND a.player = ? AND a.action IN ('call','bet','raise')) THEN 1 ELSE 0 END AS vpip,
               CASE WHEN EXISTS (SELECT 1 FROM actions a WHERE a.hand_id = hh.hand_id AND a.street = 'preflop' AND a.player = ? AND a.action IN ('bet','raise')) THEN 1 ELSE 0 END AS pfr
        FROM hero_hands hh
    )
    SELECT ha.hero_position AS position,
           AVG(ha.vpip) * 100 AS vpip_percent,
           AVG(ha.pfr) * 100 AS pfr_percent
    FROM hero_actions ha
    GROUP BY ha.hero_position
    """

    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row

            # Overall stats
            overall_row = conn.execute(overall_sql, (hero_name,)).fetchone()
            overall = dict(overall_row) if overall_row else {}

            # VPIP/PFR by position
            vpip_pfr_rows = conn.execute(vpip_pfr_sql, (hero_name, hero_name, hero_name)).fetchall()
            vpip_pfr = [dict(r) for r in vpip_pfr_rows]

            # Tournament vs cash
            tc_sql = """
            WITH hand_results AS (
                SELECT h.hand_id,
                       h.is_tournament,
                       CASE WHEN h.is_tournament = 1 THEN 'tournament' ELSE 'cash' END AS game_type,
                       (SELECT p.stack FROM players p WHERE p.hand_id = h.hand_id AND p.is_hero = 1) AS hero_start_stack,
                       h.hero_won
                FROM hands h
                JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
                WHERE p.name = ?
            ),
            bb_calculated AS (
                SELECT hr.game_type,
                       SUM(hr.hero_won) / NULLIF(SUM(hr.hero_start_stack), 0) * 100 AS bb_per_hand
                FROM hand_results hr
                GROUP BY hr.game_type
            )
            SELECT bc.game_type,
                   ROUND(bc.bb_per_hand * 100, 2) AS bb_per_100_hands
            FROM bb_calculated bc
            """
            tc_rows = conn.execute(tc_sql, (hero_name,)).fetchall()
            tc_comparison = [dict(r) for r in tc_rows]

            # ROI in tournaments
            roi_sql = """
            WITH tourney_hands AS (
                SELECT h.hand_id,
                       h.tournament_id,
                       CAST(REPLACE(REPLACE(h.buy_in, '$', ''), ',', '') AS REAL) AS buy_in_amount,
                       h.hero_won
                FROM hands h
                JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1
                WHERE p.name = ?
                  AND h.is_tournament = 1
                  AND h.buy_in IS NOT NULL
            ),
            agg AS (
                SELECT th.tournament_id,
                       SUM(th.hero_won) AS total_won,
                       SUM(th.buy_in_amount) AS total_buy_in
                FROM tourney_hands th
                GROUP BY th.tournament_id
            )
            SELECT ROUND(AVG((a.total_won - a.total_buy_in) / NULLIF(a.total_buy_in, 0) * 100), 2) AS average_roi_percent
            FROM agg a
            """
            roi_row = conn.execute(roi_sql, (hero_name,)).fetchone()
            roi = dict(roi_row) if roi_row else {}

            return {
                "hero": hero_name,
                "total_hands": overall.get("total_hands", 0),
                "overall": {
                    "win_rate_percent": round(overall.get("win_rate_percent", 0), 2),
                    "avg_bb_per_hand": round(overall.get("avg_bb_per_hand", 0), 2),
                    "total_bb_won": round(overall.get("total_bb_won", 0), 2)
                },
                "positional_stats": vpip_pfr,
                "game_type_comparison": tc_comparison,
                "tournament_roi": roi.get("average_roi_percent", 0)
            }
        finally:
            conn.close()


# ===== END NEW MCP QUERIES =====


if __name__ == "__main__":
    transport = os.environ.get("LEAKSNIPE_MCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        import uvicorn
        from starlette.applications import Starlette

        port = int(os.environ.get("LEAKSNIPE_MCP_PORT", "8001"))
        # Build Starlette MCP app for streamable-http
        stream_app = mcp.http_app(
            path="/mcp",
            transport="streamable-http",
            json_response=True,
            stateless_http=True,
            host_origin_protection=False,
        )
        # Build Starlette MCP app for sse
        sse_app = mcp.http_app(
            path="/sse",
            transport="sse",
            host_origin_protection=False,
        )
        # Combine routes
        app = Starlette(routes=stream_app.routes + sse_app.routes, lifespan=stream_app.lifespan)
        app = _GrokHeaderMiddleware(app)

        print(f"LeakSnipe MCP (Grok/Claude compatible) on http://127.0.0.1:{port} (serving /mcp and /sse)")
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")