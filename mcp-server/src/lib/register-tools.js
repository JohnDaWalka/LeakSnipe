/**
 * Register all LeakSnipe MCP tools (v2 schemas + options).
 */
import {
  MCP_VERSION,
  POSITIONS,
  SITES,
  GAME_TYPES,
  filterProperties,
  includeDetailProperties,
  pickFilterArgs,
  clampLimit,
  clampOffset,
  okList,
  okOne,
  okStats,
  shapeHand,
  shapeHands,
  parseCardPattern,
  buildHandWhere,
  buildHandQuery,
  applyHasMore,
  assertSafeSql,
  ensureLimit,
  expandPlayerAliases,
  computeSessions,
  extractHandMeta,
  validateHandMeta,
  validateHandData,
  dbProxyHeaders,
  dbQuery,
  requireD1,
  d1All,
  d1Run,
  d1First,
  COACHING_SCHEMA,
  getOrComputeAnalytics,
  queryHands,
  proxyLocalMcp,
  HAND_HISTORY_BUCKETS,
  BACKFILL_BATCH_SIZE,
  BACKFILL_MAX_PARSE_BYTES,
  HAND_SUMMARY_COLS,
  DEFAULT_SQL_MAX_ROWS,
} from './core.js';

export { extractHandMeta, HAND_HISTORY_BUCKETS, MCP_VERSION };

async function backfillBucket(env, bucketCfg, cursor, batch) {
  const r2 = env[bucketCfg.binding];
  if (!r2) {
    return {
      processed: 0,
      skipped: 0,
      cursor: null,
      done: true,
      error: `Missing binding ${bucketCfg.binding}`,
    };
  }
  const list = await r2.list({ cursor: cursor || undefined, limit: batch || BACKFILL_BATCH_SIZE });
  let processed = 0;
  let skipped = 0;
  for (const obj of list.objects) {
    const kvKey = `meta:${bucketCfg.alias}:${obj.key}`;
    const existing = await env.HAND_HISTORY_KV.get(kvKey);
    if (existing) {
      skipped++;
      continue;
    }
    let meta = null;
    if (obj.size <= BACKFILL_MAX_PARSE_BYTES) {
      const body = await r2.get(obj.key);
      if (body) meta = extractHandMeta(obj.key, await body.text());
    }
    if (!meta) {
      meta = {
        source_key: obj.key,
        game_type: null,
        stakes: null,
        date: null,
        players: [],
        site: null,
        parse_skipped: true,
      };
    }
    meta.size = obj.size;
    meta.bucket = bucketCfg.alias;
    if (Array.isArray(meta.players)) meta.players = meta.players.slice(0, 20);
    await env.HAND_HISTORY_KV.put(kvKey, JSON.stringify(meta), { metadata: meta });
    processed++;
  }
  return {
    processed,
    skipped,
    cursor: list.truncated ? list.cursor : null,
    done: !list.truncated,
  };
}

function listFilterProps(extra = {}) {
  return { ...filterProperties, ...extra };
}

export function registerAllTools(server) {
        // hero_times_3bet_or_more is a per-hand indicator (1 or 0 per hand,
        // then aggregated into a %, same convention as vpip_pct/pfr_pct
        // above) counting hands where the HERO's own preflop raise was itself
        // a re-raise (a prior preflop raise by anyone already existed at a
        // lower sequence) — a 3-bet, 4-bet, etc. Named "hero_*" specifically
        // so it isn't mistaken for a raw/table-wide 3-bet frequency: the
        // previous version counted total preflop bet/raise actions by ANYONE
        // in the hand, which measured "the hand saw multiple raises," not
        // the hero's own 3-bet frequency.
        const heroThreeBetStats = await dbQuery(
          env,
          `SELECT
            COUNT(*) AS total_hands_preflop,
            SUM(CASE WHEN EXISTS (
              SELECT 1 FROM actions a2 WHERE a2.hand_id = h.hand_id AND a2.street = 'Preflop'
                AND a2.player = p.name AND a2.action = 'raise'
                AND EXISTS (
                  SELECT 1 FROM actions a3 WHERE a3.hand_id = a2.hand_id AND a3.street = 'Preflop'
                    AND a3.action = 'raise' AND a3.sequence < a2.sequence
                )
            ) THEN 1 ELSE 0 END) AS hero_times_3bet_or_more
          FROM hands h
          JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1 AND p.name = ?
          WHERE h.date >= datetime('now', ?)
            AND EXISTS (SELECT 1 FROM actions a1 WHERE a1.hand_id = h.hand_id AND a1.street = 'Preflop' AND a1.player = p.name)`,
          [playerName, range]
        );
        // "Went to showdown" = a non-fold action on the River — same
        // convention analysis.py's LeakEngine uses (there is no 'showdown'
        // street; that comparison in the original never matched anything).
        const showdownStats = await dbQuery(
          env,
          `SELECT
            COUNT(*) AS hands_showdown,
            SUM(CASE WHEN h.hero_won > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS showdown_winrate
          FROM hands h
          JOIN players p ON p.hand_id = h.hand_id AND p.is_hero = 1 AND p.name = ?
          WHERE h.date >= datetime('now', ?)
            AND EXISTS (
              SELECT 1 FROM actions a WHERE a.hand_id = h.hand_id AND a.street = 'River'
                AND a.player = p.name AND a.action != 'fold'
            )`,
          [playerName, range]
        );

        const basic = basicStats.results?.[0] || {};
        const positions = positionStats.results || [];
        const heroThreeBet = heroThreeBetStats.results?.[0] || {};
        const showdown = showdownStats.results?.[0] || {};
        const leaks = [];
        const RANGES = {
          UTG: [8, 18], 'UTG+1': [8, 18], 'UTG+2': [9, 20], MP: [10, 22], HJ: [11, 24],
          CO: [12, 26], BTN: [15, 30], SB: [12, 28], BB: [10, 25],
        };
        positions.forEach((pos) => {
          const vpip = parseFloat(pos.vpip_pct) || 0;
          const pfr = parseFloat(pos.pfr_pct) || 0;
          const [minVPIP, maxVPIP] = RANGES[pos.position] || [10, 30];
          if (vpip > maxVPIP) {
            leaks.push({ type: 'VPIP_TOO_HIGH', position: pos.position, current: vpip.toFixed(1), recommended: maxVPIP, severity: 'HIGH', description: `Playing too many hands from ${pos.position} (VPIP ${vpip}% > ${maxVPIP}% max)` });
          } else if (vpip < minVPIP) {
            leaks.push({ type: 'VPIP_TOO_LOW', position: pos.position, current: vpip.toFixed(1), recommended: minVPIP, severity: 'MEDIUM', description: `Playing too few hands from ${pos.position} (VPIP ${vpip}% < ${minVPIP}% min)` });
          }
          if (vpip > 0) {
            const aggressionPct = (pfr / vpip) * 100;
            if (aggressionPct < 40) {
              leaks.push({ type: 'NOT_AGGRESSIVE_ENOUGH', position: pos.position, current: aggressionPct.toFixed(1), recommended: '60-80', severity: 'MEDIUM', description: `Not aggressive enough from ${pos.position} (PFR/VPIP ratio ${aggressionPct.toFixed(1)}% < 40%)` });
            } else if (aggressionPct > 90) {
              leaks.push({ type: 'TOO_AGGRESSIVE', position: pos.position, current: aggressionPct.toFixed(1), recommended: '60-80', severity: 'LOW', description: `Possibly too aggressive from ${pos.position} (PFR/VPIP ratio ${aggressionPct.toFixed(1)}% > 90%)` });
            }
          }
        });
        const totalHandsPreflop = parseFloat(heroThreeBet.total_hands_preflop) || 0;
        const heroTimes3bet = parseFloat(heroThreeBet.hero_times_3bet_or_more) || 0;
        const threeBetPct = totalHandsPreflop > 0 ? (heroTimes3bet / totalHandsPreflop) * 100 : 0;
        if (threeBetPct < 3) {
          leaks.push({ type: 'THREE_BET_TOO_LOW', current: threeBetPct.toFixed(2), recommended: '3-8', severity: 'MEDIUM', description: `3-bet frequency too low (${threeBetPct.toFixed(2)}% < 3%)` });
        } else if (threeBetPct > 10) {
          leaks.push({ type: 'THREE_BET_TOO_HIGH', current: threeBetPct.toFixed(2), recommended: '3-8', severity: 'LOW', description: `3-bet frequency possibly too high (${threeBetPct.toFixed(2)}% > 10%)` });
        }
        const showdownWinrate = parseFloat(showdown.showdown_winrate) || 0;
        const handsShowdown = parseFloat(showdown.hands_showdown) || 0;
        if (handsShowdown >= 20) {
          if (showdownWinrate < 45) {
            leaks.push({ type: 'SHOWDOWN_WINRATE_TOO_LOW', current: showdownWinrate.toFixed(1), recommended: '45-55', severity: 'HIGH', description: `Showdown win rate too low (${showdownWinrate.toFixed(1)}% < 45%)` });
          } else if (showdownWinrate > 55) {
            leaks.push({ type: 'SHOWDOWN_WINRATE_TOO_HIGH', current: showdownWinrate.toFixed(1), recommended: '45-55', severity: 'LOW', description: `Showdown win rate suspiciously high (${showdownWinrate.toFixed(1)}% > 55%) - might be running hot` });
          }
        }
        return {
          basic_stats: basic,
          position_stats: positions,
          three_bet_pct: Number(threeBetPct.toFixed(2)),
          showdown_stats: showdown,
          leaks,
          note: 'total_profit/avg_profit_per_hand are chip/tournament units unless every hand in range is cash.',
        };
      });
    }
  );

