import { useState, useEffect } from 'react';
import { AlertTriangle, TrendingUp, TrendingDown, Activity, Shield } from 'lucide-react';

const STAT_LABELS: Record<string, { label: string; unit: string; optMin: number; optMax: number }> = {
  vpip: { label: 'VPIP', unit: '%', optMin: 20, optMax: 28 },
  pfr: { label: 'PFR', unit: '%', optMin: 15, optMax: 22 },
  threeBet: { label: '3-Bet', unit: '%', optMin: 6, optMax: 10 },
  af: { label: 'Agg Factor', unit: '', optMin: 2.0, optMax: 3.5 },
  wtsd: { label: 'WTSD', unit: '%', optMin: 25, optMax: 32 },
  wsd: { label: 'W$SD', unit: '%', optMin: 48, optMax: 56 },
  riverCall: { label: 'River Call', unit: '%', optMin: 20, optMax: 35 },
};

const TILT_ICONS: Record<string, string> = {
  loss_streak: '🔥', bad_beat: '💀', vpip_spike: '📈', af_spike: '⚡',
  rapid_play: '⏱️', revenge_tilt: '😤',
};

export default function LeakDetector() {
  const [stats, setStats] = useState<any>(null);
  const [tiltFlags, setTiltFlags] = useState<any[]>([]);
  const [leaks, setLeaks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    const [s, tf, lk] = await Promise.all([
      window.pokerAPI.getLeakStats(),
      window.pokerAPI.getTiltFlags(),
      window.pokerAPI.getLeaks(),
    ]);
    setStats(s);
    setTiltFlags(tf || []);
    setLeaks(lk || []);
    setLoading(false);
  }

  function statColor(key: string, val: number): string {
    const opt = STAT_LABELS[key];
    if (!opt) return 'text-gray-400';
    if (val >= opt.optMin && val <= opt.optMax) return 'text-green-400';
    const dist = val < opt.optMin ? opt.optMin - val : val - opt.optMax;
    return dist > 10 ? 'text-red-400' : 'text-yellow-400';
  }

  function severityColor(sev: string): string {
    if (sev === 'high') return 'bg-red-900/40 border-red-600';
    if (sev === 'medium') return 'bg-yellow-900/30 border-yellow-600';
    return 'bg-blue-900/20 border-blue-600';
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full text-gray-500"><Activity className="animate-spin mr-2" size={20} /> Loading leak data…</div>;
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2"><Shield size={24} /> Leak Detector</h2>
        <button onClick={loadData} className="text-sm bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded">Refresh</button>
      </div>

      {/* Stat Gauges */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {Object.entries(STAT_LABELS).map(([key, meta]) => {
          const val = stats?.[key] ?? 0;
          const display = meta.unit === '%' ? val.toFixed(1) + '%' : val.toFixed(2);
          return (
            <div key={key} className="bg-gray-800 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-500 mb-1">{meta.label}</div>
              <div className={`text-xl font-bold ${statColor(key, val)}`}>{display}</div>
              <div className="text-[10px] text-gray-600 mt-1">Opt: {meta.optMin}–{meta.optMax}{meta.unit}</div>
            </div>
          );
        })}
      </div>

      {/* Extra stats row */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-500">Win Rate</div>
            <div className={`text-lg font-bold ${(stats.winRate || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {((stats.winRate || 0) * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-500">bb/100</div>
            <div className={`text-lg font-bold ${(stats.bb100 || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {(stats.bb100 || 0).toFixed(1)}
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-500">Hands Analyzed</div>
            <div className="text-lg font-bold text-white">{stats.totalHands || 0}</div>
          </div>
        </div>
      )}

      {/* Tilt Flags */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <AlertTriangle size={18} className="text-yellow-400" /> Tilt Flags ({tiltFlags.length})
        </h3>
        {tiltFlags.length === 0 ? (
          <p className="text-gray-500 text-sm">No tilt flags detected — playing solid! ✅</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {tiltFlags.map((tf, i) => (
              <div key={i} className="flex items-center gap-3 bg-gray-800 rounded-lg px-4 py-3">
                <span className="text-2xl">{TILT_ICONS[tf.type] || '⚠️'}</span>
                <div className="flex-1">
                  <div className="text-sm font-medium text-white capitalize">{tf.type.replace(/_/g, ' ')}</div>
                  <div className="text-xs text-gray-500">{tf.description || `Detected at hand ${tf.handIndex || '?'}`}</div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  tf.severity === 'high' ? 'bg-red-700 text-red-200' :
                  tf.severity === 'medium' ? 'bg-yellow-700 text-yellow-200' : 'bg-blue-700 text-blue-200'
                }`}>{tf.severity || 'low'}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Identified Leaks */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <TrendingDown size={18} className="text-red-400" /> Identified Leaks ({leaks.length})
        </h3>
        {leaks.length === 0 ? (
          <p className="text-gray-500 text-sm">No significant leaks detected — great play! 🎯</p>
        ) : (
          <div className="space-y-2">
            {leaks.map((lk, i) => (
              <div key={i} className={`rounded-lg border px-4 py-3 ${severityColor(lk.severity)}`}>
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-white">{lk.stat}: {lk.value?.toFixed?.(1) ?? lk.value}</div>
                  <span className={`text-xs uppercase font-bold ${
                    lk.severity === 'high' ? 'text-red-400' : lk.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                  }`}>{lk.severity}</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">{lk.advice}</p>
                <div className="text-[10px] text-gray-600 mt-1">
                  Optimal: {lk.optimalRange?.[0]}–{lk.optimalRange?.[1]} | Your value: {lk.value?.toFixed?.(2) ?? lk.value}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
