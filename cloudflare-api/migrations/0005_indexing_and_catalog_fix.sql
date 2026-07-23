-- Migration 0005: Indexing Optimization & Schema Catalog Alignment
-- Fixes missing indexes identified in query profiling (tournament_id, winners, hand_tags, actions, player_types)

-- 1. Index on hands(tournament_id) to convert 6,800+ row full table scans into 150-row index lookups
CREATE INDEX IF NOT EXISTS idx_hands_tournament_id ON hands (tournament_id);
CREATE INDEX IF NOT EXISTS idx_hands_tournament_date ON hands (tournament_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_hands_site_is_mtt_date ON hands (site, is_tournament, date DESC);

-- 2. Index on winners(hand_id) for fast winner lookup joins
CREATE INDEX IF NOT EXISTS idx_winners_hand_id ON winners (hand_id);

-- 3. Index on hand_tags(tag) for tag filtering
CREATE INDEX IF NOT EXISTS idx_hand_tags_tag ON hand_tags (tag);

-- 4. Covering index on actions(hand_id, street, sequence)
CREATE INDEX IF NOT EXISTS idx_actions_hand_street_seq ON actions (hand_id, street, sequence);

-- 5. Index on player_types for lower(name) lookups
CREATE INDEX IF NOT EXISTS idx_player_types_name ON player_types (name);

-- 6. Register sessions table in schema_catalog and update database_name default to leaksnipe-hands
INSERT OR REPLACE INTO schema_catalog (table_name, database_name, description, columns_json, updated_at)
VALUES (
  'sessions',
  'leaksnipe-hands',
  'Sit-down session summaries aggregated by site and gap boundary (default 30 min).',
  '{"columns": ["session_id", "site", "start_time", "end_time", "hands_count", "net_won", "bb_per_100", "is_tournament", "created_at"]}',
  datetime('now')
);

UPDATE schema_catalog SET database_name = 'leaksnipe-hands' WHERE database_name = 'poker_hands';
