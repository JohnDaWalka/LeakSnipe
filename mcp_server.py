import sys
import os
import json
import sqlite3
import traceback
from datetime import datetime

# Add REPO_ROOT and sidecar folder to import search path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
sidecar_dir = os.path.join(REPO_ROOT, "sidecar")
if sidecar_dir not in sys.path:
    sys.path.insert(0, sidecar_dir)

# Redirect stdout print statements to stderr to prevent corrupting JSON-RPC on stdout
def log_err(msg):
    sys.stderr.write(f"[LeakSnipe-MCP] {msg}\n")
    sys.stderr.flush()

try:
    from models import HandDatabase, Hand
    from paths import resolve_db_path
    from config import load_settings
    from utils import resolve_hand_hero_name
    from coach_memory import CoachMemory, DEFAULT_MEMORY_DB
except Exception as e:
    log_err(f"Imports failed: {e}\n{traceback.format_exc()}")
    sys.exit(1)

def get_db():
    try:
        settings = load_settings()
        db_path = resolve_db_path(settings)
        return HandDatabase(db_path), settings
    except Exception as e:
        log_err(f"Failed to connect to database: {e}")
        raise

def serialize_hand(hand: Hand, settings: dict, *, format: str = "summary", include_raw: bool = False) -> dict:
    """Default format=summary omits raw_text/streets to save agent context."""
    hero_name = resolve_hand_hero_name(
        settings,
        hand.site,
        players=hand.players,
        raw_text=hand.raw_text,
        hero_player=getattr(hand, "hero_player", ""),
    )
    date_str = hand.date.isoformat() if hand.date else None
    full = format == "full" or include_raw
    out = {
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
    }
    if full:
        out["players"] = [
            {
                "seat": seat,
                "name": p["name"],
                "stack": p["stack"],
                "is_hero": p.get("is_hero", False),
            }
            for seat, p in hand.players.items()
        ]
        out["streets"] = [
            {
                "name": street.get("name", ""),
                "cards": street.get("cards", []),
                "actions": [
                    {
                        "player": act.get("player", ""),
                        "action": act.get("action", ""),
                        "amount": act.get("amount", 0.0),
                    }
                    for act in street.get("actions", [])
                ],
            }
            for street in getattr(hand, "streets", [])
        ]
        out["winners"] = [
            {"name": w["name"], "amount": w["amount"]}
            for w in getattr(hand, "winners", [])
        ]
        out["raw_text"] = hand.raw_text
    return out

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
    sit-down grouping using the same gap-based heuristic as calculate_sessions/
    get_sessions_winrate (default 30min gap). Must run over the FULL, unfiltered hand
    history per site (LAG needs the true previous hand's date) — any caller-supplied
    filter has to be applied outside this CTE (`SELECT * FROM session_hands WHERE ...`),
    never folded into it, or the gap calculation silently breaks (windowing over an
    already-filtered subset collapses everything into session_id=1). Computed at query
    time, not persisted, so it can't drift from that shared definition.

    Split into two CTE steps (gaps, then session_hands) rather than nesting LAG()
    directly inside SUM()'s argument — SQLite rejects a window function used as an
    input expression to another window function in the same SELECT ("misuse of window
    function LAG()"), verified against sqlite3 3.45.1 locally. The pre-existing
    get_sessions_winrate/calculate_sessions queries have this same nested pattern and
    hit the same error — out of scope here, but worth fixing separately."""
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
            fmt = "summary"
            serialized = [serialize_hand(h, settings, format=fmt) for h in hands]
            if session_ids:
                for s in serialized:
                    s["session_id"] = session_ids.get(s.get("hand_id"))
            return serialized
        finally:
            conn.close()

def get_live_table_state(db, settings, site=None, table=None):
    """Latest imported hand's seat map — mirrors sidecar/server.py's live_current_hand().
    Note: hand histories only land after a hand completes, so this reflects the latest
    completed hand, not a mid-hand snapshot — stacks are that hand's starting stacks."""
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
            "seat_map": {}, "opponents": [], "table_name": None,
        }

    seat_map = {}
    opponents = []
    for seat, info in sorted(hand.players.items()):
        name = str(info.get("name") or "").strip()
        is_hero = bool(info.get("is_hero")) or name in heroes
        seat_map[str(seat)] = {"name": name, "is_hero": is_hero, "stack": info.get("stack")}
        if name and not is_hero:
            opponents.append(name)

    return {
        "ok": True,
        "hand_id": hand.hand_id,
        "site": hand.site,
        "max_seats": hand.max_seats or 6,
        "seat_map": seat_map,
        "opponents": opponents,
        "table_name": hand.table_name,
    }


def calculate_sessions(db, settings, site=None, gap_minutes=30, limit=10):
    from collections import defaultdict
    sql = "SELECT hand_id, date, site, hero_won, is_tournament, hero_position FROM hands"
    params = []
    where_clauses = []
    if site:
        where_clauses.append("site = ?")
        params.append(site)
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    sql += " ORDER BY date ASC"
    
    with db.lock:
        conn = db._connect()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
            
    if not rows:
        return []
        
    hands_by_site = defaultdict(list)
    for r in rows:
        hands_by_site[r["site"]].append(r)
        
    sessions = []
    gap_seconds = gap_minutes * 60
    
    for current_site, site_hands in hands_by_site.items():
        if not site_hands:
            continue
            
        current_session = []
        last_time = None
        
        for h in site_hands:
            h_date_str = h["date"]
            if not h_date_str:
                continue
            try:
                h_date = datetime.fromisoformat(h_date_str)
            except Exception:
                continue
                
            if last_time is not None:
                diff = (h_date - last_time).total_seconds()
                if diff > gap_seconds:
                    sessions.append((current_site, current_session))
                    current_session = []
            
            current_session.append({
                "hand_id": h["hand_id"],
                "date": h_date,
                "hero_won": h["hero_won"] or 0.0,
                "is_tournament": bool(h["is_tournament"]),
                "position": h["hero_position"]
            })
            last_time = h_date
            
        if current_session:
            sessions.append((current_site, current_session))
            
    summary_sessions = []
    for idx, (sess_site, sess) in enumerate(sessions):
        if not sess:
            continue
        first_hand = sess[0]
        last_hand = sess[-1]
        
        hand_count = len(sess)
        total_won = sum(h["hero_won"] for h in sess)
        won_hands = sum(1 for h in sess if h["hero_won"] > 0)
        lost_hands = sum(1 for h in sess if h["hero_won"] < 0)
        
        duration = (last_hand["date"] - first_hand["date"]).total_seconds()
        duration_minutes = round(duration / 60, 1)
        
        winrate_pct = round((won_hands / hand_count) * 100, 1) if hand_count > 0 else 0.0
        
        summary_sessions.append({
            "session_index": idx + 1,
            "site": sess_site,
            "start_time": first_hand["date"].isoformat(),
            "end_time": last_hand["date"].isoformat(),
            "hand_count": hand_count,
            "net_profit": round(total_won, 2),
            "won_hands": won_hands,
            "lost_hands": lost_hands,
            "winrate_pct": winrate_pct,
            "duration_minutes": duration_minutes,
            "hands_per_hour": round(hand_count / (duration / 3600), 1) if duration > 60 else hand_count
        })
        
    summary_sessions.sort(key=lambda s: s["start_time"], reverse=True)
    return summary_sessions[:limit]

def exec_cmd(cmd_list, cwd=None):
    try:
        import subprocess
        cmd_str = " ".join(cmd_list)
        res = subprocess.run(
            cmd_str,
            cwd=cwd,
            shell=True,
            capture_output=True,
            timeout=30
        )
        
        def safe_decode(b):
            if not b:
                return ""
            for encoding in ['utf-8', 'cp1252', 'cp850']:
                try:
                    return b.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return b.decode('utf-8', errors='replace')

        return {
            "stdout": safe_decode(res.stdout),
            "stderr": safe_decode(res.stderr),
            "exit_code": res.returncode
        }
    except Exception as e:
        return {
            "error": str(e)
        }

def handle_request(req):
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "LeakSnipe MCP Server",
                    "version": "2.0.0"
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "get_all_heroes",
                        "description": "List all hero/user names registered in the tracker database (e.g. gboss101, jdwalka).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_totals_stats",
                        "description": "Retrieve aggregate statistics (total hands, collected, lost, net profit) from the database.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "site": {"type": "string", "description": "Filter by site ('CoinPoker' or 'BetACR')"},
                                "tag": {"type": "string", "description": "Filter by custom tag"},
                                "user": {"type": "string", "description": "Filter by hero name ('Gboss101' or 'jdwalka')"},
                                "start_date": {"type": "string", "description": "ISO format start date (YYYY-MM-DD)"},
                                "end_date": {"type": "string", "description": "ISO format end date (YYYY-MM-DD)"}
                            }
                        }
                    },
                    {
                        "name": "search_hands",
                        "description": "Natural language search across hands (e.g. 'my last 3-bet pot from cutoff')",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language search query like '3-bet from cutoff'"},
                                "limit": {"type": "integer", "description": "Max hands to return (default 10)"},
                                "offset": {"type": "integer", "description": "Pagination offset"},
                                "gap_minutes": {"type": "integer", "description": "Session-boundary gap in minutes for the computed session_id (default 30)"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_recent_hands",
                        "description": "Returns the most recent hands played by the user",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer", "description": "Max hands to return (default 10)"},
                                "since": {"type": "string", "description": "ISO timestamp (YYYY-MM-DD) to get hands after"},
                                "gap_minutes": {"type": "integer", "description": "Session-boundary gap in minutes for the computed session_id (default 30)"}
                            }
                        }
                    },
                    {
                        "name": "get_hands_by_cards",
                        "description": "Returns hands containing specific hole cards (e.g. 'QQ', 'AKs', '76s')",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "cards": {"type": "string", "description": "Card string like 'QQ', 'AK', '76s'"},
                                "limit": {"type": "integer", "description": "Max hands to return (default 10)"}
                            },
                            "required": ["cards"]
                        }
                    },
                    {
                        "name": "get_biggest_winning_hands",
                        "description": "Returns the biggest winning hands by profit",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer", "description": "Max hands to return (default 10)"}
                            }
                        }
                    },
                    {
                        "name": "get_winrate_by_position",
                        "description": "Returns winrate statistics broken down by position",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_hands_by_position",
                        "description": "Returns hands played from a specific position",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "position": {"type": "string", "enum": ["UTG","MP","HJ","CO","BTN","SB","BB"], "description": "Table position"},
                                "limit": {"type": "integer", "description": "Max hands to return (default 10)"}
                            },
                            "required": ["position"]
                        }
                    },
                    {
                        "name": "get_hand_detail",
                        "description": "Retrieve the complete action-by-action detail and raw hand history log for a specific hand ID.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hand_id": {"type": "string", "description": "The unique hand ID"}
                            },
                            "required": ["hand_id"]
                        }
                    },
                    {
                        "name": "get_hand_by_number",
                        "description": "Get exactly one hand by its hand_number (reliable single-hand lookup — use this instead of get_hand_detail/search_hands when you know the hand number, not the internal hand_id). Pass site and/or tournament_id to disambiguate if the same hand_number appears more than once.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hand_number": {"type": "string", "description": "The hand_number to look up, e.g. '96'"},
                                "site": {"type": "string", "description": "Optional site filter to disambiguate (e.g. 'BetACR', 'CoinPoker')"},
                                "tournament_id": {"type": "string", "description": "Optional tournament_id filter to disambiguate"},
                                "gap_minutes": {"type": "integer", "description": "Session-boundary gap in minutes for the computed session_id (default 30)"}
                            },
                            "required": ["hand_number"]
                        }
                    },
                    {
                        "name": "add_tag",
                        "description": "Tag a specific hand with a label.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hand_id": {"type": "string", "description": "The unique hand ID"},
                                "tag": {"type": "string", "description": "Custom label to add"}
                            },
                            "required": ["hand_id", "tag"]
                        }
                    },
                    {
                        "name": "remove_tag",
                        "description": "Remove a tag from a specific hand.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hand_id": {"type": "string", "description": "The unique hand ID"},
                                "tag": {"type": "string", "description": "Custom label to remove"}
                            },
                            "required": ["hand_id", "tag"]
                        }
                    },
                    {
                        "name": "get_sessions_winrate",
                        "description": "Calculate poker sessions dynamically based on gap minutes and return session winrate, profit, and duration.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "site": {"type": "string", "description": "Filter by poker site (e.g. 'CoinPoker', 'BetACR')"},
                                "gap_minutes": {"type": "integer", "description": "Minutes gap between hands to define a new session (default 30)"},
                                "limit": {"type": "integer", "description": "Max sessions to return (default 10)"}
                            }
                        }
                    },
                    {
                        "name": "get_live_table_read",
                        "description": "Live read on the current table: seats/last-known stacks from the most recently imported hand, plus career VPIP/PFR/AF/WTSD/3-bet for every opponent currently seated. Note: hand histories only land after a hand completes, so this reflects the latest completed hand, not a mid-hand snapshot.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "site": {"type": "string", "description": "Optional site filter (e.g. 'BetACR', 'CoinPoker')"},
                                "table": {"type": "string", "description": "Optional table name/tournament_id filter"}
                            }
                        }
                    },
                    {
                        "name": "write_coach_memory",
                        "description": "Persist a coaching note or dialogue turn to the local coach_memory store (and, if the Cloudflare tunnel is up, sync it to D1/KV so it's cross-session visible remotely too).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hero": {"type": "string", "description": "Hero this note is about (e.g. 'jdwalka', 'Gboss101')"},
                                "kind": {"type": "string", "description": "Type of entry, e.g. 'note' or 'turn'", "default": "note"},
                                "user_text": {"type": "string", "description": "The user-side text (question, hand context, etc.)"},
                                "assistant_text": {"type": "string", "description": "The coaching note / observation to persist"},
                                "provider": {"type": "string", "description": "Which agent wrote this: 'claude' or 'grok'"}
                            },
                            "required": ["hero", "assistant_text", "provider"]
                        }
                    },
                    {
                        "name": "d1_coach_memory",
                        "description": "Read coach_memory dialogue history for a hero (cross-session coaching context) from the local coach_memory store.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hero": {"type": "string", "description": "Hero name filter"},
                                "limit": {"type": "integer", "description": "Max entries to return (default 20)"}
                            }
                        }
                    },
                    {
                        "name": "run_network_command",
                        "description": "Execute network diagnostics and tools (ipconfig, ping, tracert, nslookup, netstat, arp, route, getmac).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string", 
                                    "enum": ["ipconfig", "ping", "tracert", "nslookup", "netstat", "arp", "route", "getmac"],
                                    "description": "Network tool to run"
                                },
                                "args": {
                                    "type": "string",
                                    "description": "Command-line arguments as a single space-separated string (e.g. 'google.com' or '-n 4 google.com')"
                                }
                            },
                            "required": ["command"]
                        }
                    },
                    {
                        "name": "run_cloudflare_command",
                        "description": "Execute Cloudflare wrangler or cloudflared commands to inspect configuration, tunnels, D1, or R2.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "enum": ["wrangler", "cloudflared"],
                                    "description": "Command to execute"
                                },
                                "args": {
                                    "type": "string",
                                    "description": "Command-line arguments as a single space-separated string (e.g. 'tunnel list' or 'whoami')"
                                },
                                "sub_project": {
                                    "type": "string",
                                    "enum": ["root", "mcp-server", "cloudflare-api", "poker-daemon-worker"],
                                    "description": "Working directory context to run wrangler command (default: 'root')"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        db, settings = get_db()

        try:
            if tool_name == "get_all_heroes":
                heroes = db.get_all_heroes()
                return json_rpc_success(req_id, {"heroes": heroes})

            elif tool_name == "get_totals_stats":
                res = db.search_hands(
                    site=args.get("site"),
                    tag=args.get("tag"),
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date"),
                    hero_name=args.get("user"),
                    limit=1,
                    offset=0
                )
                return json_rpc_success(req_id, {"totals": res["totals"]})

            elif tool_name == "search_hands":
                query = args.get("query", "")
                limit = min(args.get("limit", 10), 100)
                offset = args.get("offset", 0)
                gap_minutes = args.get("gap_minutes", 30)
                where_str, sql_params, parsed_limit = parse_natural_language_query(query)
                if not args.get("limit"):
                    limit = parsed_limit
                sql = f"{session_id_cte(gap_minutes)} SELECT * FROM session_hands{where_str} ORDER BY date DESC LIMIT ? OFFSET ?"
                hands = query_and_serialize_hands(db, settings, sql, sql_params + [limit, offset])
                return json_rpc_success(req_id, {"hands": hands})

            elif tool_name == "get_recent_hands":
                limit = min(args.get("limit", 10), 100)
                since = args.get("since")
                gap_minutes = args.get("gap_minutes", 30)
                where_clauses = []
                sql_params = []
                if since:
                    where_clauses.append("date >= ?")
                    sql_params.append(since)
                where_str = ""
                if where_clauses:
                    where_str = " WHERE " + " AND ".join(where_clauses)
                sql = f"{session_id_cte(gap_minutes)} SELECT * FROM session_hands{where_str} ORDER BY date DESC LIMIT ?"
                hands = query_and_serialize_hands(db, settings, sql, sql_params + [limit])
                return json_rpc_success(req_id, {"hands": hands})

            elif tool_name == "get_hands_by_cards":
                cards = args.get("cards", "")
                limit = min(args.get("limit", 10), 100)
                cards_sql, cards_params = build_cards_sql(cards)
                if not cards_sql:
                    return json_rpc_error(req_id, -32602, "Invalid cards specified")
                sql = f"SELECT * FROM hands WHERE {cards_sql} ORDER BY date DESC LIMIT ?"
                hands = query_and_serialize_hands(db, settings, sql, cards_params + [limit])
                return json_rpc_success(req_id, {"hands": hands})

            elif tool_name == "get_biggest_winning_hands":
                limit = min(args.get("limit", 10), 100)
                sql = "SELECT * FROM hands WHERE hero_won > 0 ORDER BY hero_won DESC LIMIT ?"
                hands = query_and_serialize_hands(db, settings, sql, [limit])
                return json_rpc_success(req_id, {"hands": hands})

            elif tool_name == "get_winrate_by_position":
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
                        stats = [dict(r) for r in rows]
                        return json_rpc_success(req_id, {"winrate_by_position": stats})
                    finally:
                        conn.close()

            elif tool_name == "get_hands_by_position":
                position = args.get("position", "").upper()
                limit = min(args.get("limit", 10), 100)
                sql = "SELECT * FROM hands WHERE UPPER(hero_position) = ? ORDER BY date DESC LIMIT ?"
                hands = query_and_serialize_hands(db, settings, sql, [position, limit])
                return json_rpc_success(req_id, {"hands": hands})

            elif tool_name == "get_hand_detail" or tool_name == "get_hand":
                hand_id = args.get("hand_id") or args.get("id")
                hand = db.get_hand_by_id(hand_id)
                if not hand:
                    return json_rpc_error(req_id, -32602, f"Hand not found: {hand_id}")
                detail = serialize_hand(
                    hand,
                    settings,
                    format=args.get("format", "full"),
                    include_raw=bool(args.get("include_raw", True)),
                )
                return json_rpc_success(req_id, {"success": True, "found": True, "result": detail, "hand": detail})

            elif tool_name == "get_hand_by_number":
                hand_number = args.get("hand_number")
                if not hand_number:
                    return json_rpc_error(req_id, -32602, "hand_number is required")
                gap_minutes = args.get("gap_minutes", 30)
                lookup = db.get_hand_by_number(
                    hand_number,
                    site=args.get("site"),
                    tournament_id=args.get("tournament_id"),
                )
                if lookup["matches"] == 1:
                    detail = serialize_hand(
                        lookup["hand"],
                        settings,
                        format=args.get("format", "full"),
                        include_raw=bool(args.get("include_raw", True)),
                    )
                    with db.lock:
                        conn = db._connect()
                        try:
                            conn.row_factory = sqlite3.Row
                            sid_row = conn.execute(
                                f"{session_id_cte(gap_minutes)} SELECT session_id FROM session_hands WHERE hand_id = ?",
                                [lookup["hand"].hand_id],
                            ).fetchone()
                            detail["session_id"] = sid_row["session_id"] if sid_row else None
                        finally:
                            conn.close()
                    return json_rpc_success(req_id, {"success": True, "found": True, "hand": detail})
                if lookup["matches"] == 0:
                    site_note = f" on site {args.get('site')}" if args.get("site") else ""
                    return json_rpc_success(req_id, {
                        "success": False,
                        "found": False,
                        "error": f"No hand found with hand_number {hand_number}{site_note}",
                    })
                return json_rpc_success(req_id, {
                    "success": False,
                    "found": False,
                    "error": f"{lookup['matches']} hands match hand_number {hand_number} — disambiguate with site and/or tournament_id",
                    "candidates": lookup["candidates"],
                })

            elif tool_name == "add_tag":
                hand_id = args.get("hand_id")
                tag = args.get("tag")
                db.add_tag(hand_id, tag)
                return json_rpc_success(req_id, {"ok": True, "tags": db.get_tags(hand_id)})

            elif tool_name == "remove_tag":
                hand_id = args.get("hand_id")
                tag = args.get("tag")
                db.remove_tag(hand_id, tag)
                return json_rpc_success(req_id, {"ok": True, "tags": db.get_tags(hand_id)})

            elif tool_name == "get_sessions_winrate":
                site = args.get("site")
                gap_minutes = args.get("gap_minutes", 30)
                limit = min(args.get("limit", 10), 100)
                sessions = calculate_sessions(db, settings, site=site, gap_minutes=gap_minutes, limit=limit)
                return json_rpc_success(req_id, {"sessions": sessions})

            elif tool_name == "get_live_table_read":
                live = get_live_table_state(db, settings, site=args.get("site"), table=args.get("table"))
                opponents_read = []
                if live.get("hand_id"):
                    with db.lock:
                        conn = db._connect()
                        try:
                            conn.row_factory = sqlite3.Row
                            for name in live.get("opponents", []):
                                row = conn.execute(
                                    "SELECT name, site, hands, vpip, pfr, af, fold_cbet, wtsd, three_bet, updated_at "
                                    "FROM player_types WHERE lower(name) = lower(?)",
                                    (name,),
                                ).fetchone()
                                opponents_read.append(
                                    {**dict(row), "found": True} if row else {"name": name, "found": False}
                                )
                        finally:
                            conn.close()
                live["opponents_read"] = opponents_read
                return json_rpc_success(req_id, live)

            elif tool_name == "write_coach_memory":
                hero = (args.get("hero") or "").strip()
                assistant_text = (args.get("assistant_text") or "").strip()
                provider = (args.get("provider") or "").strip()
                kind = args.get("kind") or "note"
                user_text = args.get("user_text") or ""
                if not hero:
                    return json_rpc_error(req_id, -32602, "hero is required")
                if not assistant_text:
                    return json_rpc_error(req_id, -32602, "assistant_text is required")
                if not provider:
                    return json_rpc_error(req_id, -32602, "provider is required (e.g. 'claude' or 'grok')")
                mem = CoachMemory()
                if kind == "turn":
                    mem.add_turn(hero, user_text, assistant_text, provider=provider)
                else:
                    mem.add_note(hero, assistant_text, kind=kind, provider=provider)
                return json_rpc_success(req_id, {"success": True, "hero": hero, "kind": kind, "provider": provider})

            elif tool_name == "d1_coach_memory":
                hero = (args.get("hero") or "").strip()
                limit = min(args.get("limit", 20), 100)
                conn = sqlite3.connect(DEFAULT_MEMORY_DB, timeout=10)
                conn.row_factory = sqlite3.Row
                try:
                    cols = "id, hero, kind, user_text, assistant_text, provider, created_at"
                    if hero:
                        rows = conn.execute(
                            f"SELECT {cols} FROM coach_memory WHERE lower(hero) LIKE lower(?) "
                            "ORDER BY created_at DESC LIMIT ?",
                            (f"%{hero}%", limit),
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            f"SELECT {cols} FROM coach_memory ORDER BY created_at DESC LIMIT ?",
                            (limit,),
                        ).fetchall()
                    return json_rpc_success(req_id, {"memories": [dict(r) for r in rows]})
                finally:
                    conn.close()

            elif tool_name == "run_network_command":
                cmd = args.get("command")
                raw_args = args.get("args")
                if cmd not in ["ipconfig", "ping", "tracert", "nslookup", "netstat", "arp", "route", "getmac"]:
                    return json_rpc_error(req_id, -32602, f"Unauthorized network command: {cmd}")
                
                import shlex
                cmd_args = shlex.split(raw_args) if raw_args else []
                clean_args = []
                import re
                for arg in cmd_args:
                    if re.match(r'^[a-zA-Z0-9\-_\.\/\\:\s\?\*]+$', arg):
                        clean_args.append(arg)
                    else:
                        return json_rpc_error(req_id, -32602, f"Invalid characters in argument: {arg}")
                
                cmd_list = [cmd] + clean_args
                res = exec_cmd(cmd_list)
                return json_rpc_success(req_id, res)

            elif tool_name == "run_cloudflare_command":
                cmd = args.get("command")
                raw_args = args.get("args")
                sub_proj = args.get("sub_project", "root")
                
                if cmd not in ["wrangler", "cloudflared"]:
                    return json_rpc_error(req_id, -32602, f"Unauthorized cloudflare command: {cmd}")
                
                proj_dir = REPO_ROOT
                if sub_proj == "mcp-server":
                    proj_dir = os.path.join(REPO_ROOT, "mcp-server")
                elif sub_proj == "cloudflare-api":
                    proj_dir = os.path.join(REPO_ROOT, "cloudflare-api")
                elif sub_proj == "poker-daemon-worker":
                    proj_dir = os.path.join(REPO_ROOT, "poker-daemon", "worker")
                
                if not os.path.isdir(proj_dir):
                    return json_rpc_error(req_id, -32602, f"Directory does not exist: {proj_dir}")
                
                import shlex
                cmd_args = shlex.split(raw_args) if raw_args else []
                clean_args = []
                import re
                for arg in cmd_args:
                    if re.match(r'^[a-zA-Z0-9\-_\.\/\\:\s=@\"\?\*]+$', arg):
                        clean_args.append(arg)
                    else:
                        return json_rpc_error(req_id, -32602, f"Invalid characters in cloudflare argument: {arg}")
                
                if cmd == "wrangler":
                    cmd_list = ["npx", "wrangler"] + clean_args
                else:
                    cmd_list = [cmd] + clean_args
                
                res = exec_cmd(cmd_list, cwd=proj_dir)
                return json_rpc_success(req_id, res)

            else:
                return json_rpc_error(req_id, -32601, f"Method not found: {tool_name}")

        except Exception as err:
            log_err(f"Error executing tool {tool_name}: {err}\n{traceback.format_exc()}")
            return json_rpc_error(req_id, -32000, str(err))

    # Respond to fallback or notifications silently
    if req_id is not None:
        return json_rpc_error(req_id, -32601, f"Method not found: {method}")
    return None

def json_rpc_success(req_id, result):
    # Formulate content response list as required by MCP tools
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    }

def json_rpc_error(req_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": code,
            "message": message
        }
    }

def main():
    log_err("LeakSnipe MCP server started on stdio.")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            req = json.loads(line)
            response = handle_request(req)
            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except Exception as e:
            log_err(f"Loop error: {e}")

if __name__ == "__main__":
    main()
