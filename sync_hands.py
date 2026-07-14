#!/usr/bin/env python3
import sqlite3
import time
import json
import os
import requests
from datetime import datetime

# --- CONFIG ---
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poker_hands.db")
API_BASE = "https://mcp.leaksnipe.win"
POLL_INTERVAL = 3  # seconds (matches your Tauri capture rate)

# --- ENSURE SYNC TRACKING TABLE ---
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _cloudflare_sync (
            hand_id TEXT PRIMARY KEY,
            synced_at TEXT,
            r2_key TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- FIND THE HANDS TABLE ---
def discover_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('_')]
    conn.close()
    return tables

def get_table_schema(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    return columns

# --- SYNC NEW HANDS ---
def get_unsynced_hands(db_path, table_name, id_column, order_by_col=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    order_clause = f"h.{order_by_col} DESC" if order_by_col else f"h.{id_column}"
    
    cursor.execute(f"""
        SELECT h.* FROM {table_name} h
        LEFT JOIN _cloudflare_sync s ON h.{id_column} = s.hand_id
        WHERE s.hand_id IS NULL
        ORDER BY {order_clause}
        LIMIT 50
    """)
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_synced(db_path, hand_id, r2_key):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO _cloudflare_sync (hand_id, synced_at, r2_key) VALUES (?, ?, ?)",
        (str(hand_id), datetime.now().isoformat(), r2_key)
    )
    conn.commit()
    conn.close()

def upload_hand(hand_id, hand_data, table_name):
    r2_key = f"hands/{table_name}/{hand_id}.json"
    
    try:
        res = requests.post(
            f"{API_BASE}/hands",
            json={"key": r2_key, "content": hand_data},
            timeout=10
        )
        if res.status_code == 200:
            print(f"  [OK] Uploaded: {r2_key}")
            return r2_key
        else:
            print(f"  [FAIL] Failed: {r2_key} - {res.status_code} {res.text}")
            return None
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        return None

# --- MAIN LOOP ---
def main():
    print("=" * 50)
    print("  LeakSnipe -> Cloudflare R2 Sync")
    print("=" * 50)
    
    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] Database not found: {DB_PATH}")
        print("Update DB_PATH in this script to point to your SQLite file.")
        return
    
    init_db(DB_PATH)
    
    # Discover tables
    tables = discover_tables(DB_PATH)
    print(f"\nFound tables: {tables}")
    
    # Find the hands table (look for one with 'hand' in the name, or use the first one)
    hands_table = None
    for t in tables:
        if 'hand' in t.lower():
            hands_table = t
            break
    if not hands_table and tables:
        hands_table = tables[0]
    
    if not hands_table:
        print("[ERROR] No tables found in database.")
        return
    
    print(f"Using table: {hands_table}")
    
    # Find the ID column
    schema = get_table_schema(DB_PATH, hands_table)
    columns = [col[1] for col in schema]
    print(f"Columns: {columns}")
    
    id_column = None
    for col in columns:
        if col.lower() in ('id', 'hand_id', 'handid', 'hand_number', 'handnumber'):
            id_column = col
            break
    if not id_column and columns:
        id_column = columns[0]
    
    print(f"ID column: {id_column}")
    
    # Resolve sorting column
    order_by_col = None
    if 'date' in [c.lower() for c in columns]:
        order_by_col = 'date'
        print("Ordering unsynced hands chronologically (newest first).")

    print(f"\nSyncing every {POLL_INTERVAL}s... Press Ctrl+C to stop.\n")
    
    total_synced = 0
    
    while True:
        try:
            hands = get_unsynced_hands(DB_PATH, hands_table, id_column, order_by_col)
            
            if hands:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(hands)} new hand(s)")
                
                for hand in hands:
                    hand_id = hand[id_column]
                    hand_dict = dict(hand)
                    hand_json = json.dumps(hand_dict, indent=2, default=str)
                    
                    r2_key = upload_hand(hand_id, hand_json, hands_table)
                    if r2_key:
                        mark_synced(DB_PATH, hand_id, r2_key)
                        total_synced += 1
                
                print(f"  Total synced: {total_synced}")
            else:
                # No new hands - wait
                pass
                
        except KeyboardInterrupt:
            print(f"\n\nStopped. Total hands synced: {total_synced}")
            break
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
