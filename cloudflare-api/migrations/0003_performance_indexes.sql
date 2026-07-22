-- Migration 0003: Performance Composite Indexes for LeakSnipe D1 Database
CREATE INDEX IF NOT EXISTS idx_hands_site_date ON hands (site, imported_at);
CREATE INDEX IF NOT EXISTS idx_hands_position_tournament ON hands (hero_position, is_tournament);
CREATE INDEX IF NOT EXISTS idx_actions_hand_street ON actions (hand_id, street);
