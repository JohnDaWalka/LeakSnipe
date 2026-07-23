-- Migration 0004: Sessions Table & Persistence for Session Winrates
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  site TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  hands_count INTEGER DEFAULT 0,
  net_won REAL DEFAULT 0.0,
  bb_per_100 REAL DEFAULT 0.0,
  is_tournament BOOLEAN DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_site_time ON sessions (site, start_time);
