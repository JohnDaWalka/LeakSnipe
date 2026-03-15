import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  Cell,
} from 'recharts';
import { TrendingUp, TrendingDown, Target, Layers, RefreshCw, Activity } from 'lucide-react';

const STREET_ORDER = ['Preflop', 'Flop', 'Turn', 'River', 'Showdown'];
const ACTION_COLORS: Record<string, string> = {
  fold: '#ef4444', call: '#3b82f6', raise: '#f59e0b',
  bet: '#10b981', check: '#6b7280', allin: '#8b5cf6', post: '#374151',
};
const DAY_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function GameplayAnalysis() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [handView, setHandView] = useState<'best' | 'worst'>('best');

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    const result = await window.pokerAPI.getGameplayAnalysis();
    setData(result);
    setLoading(false);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <Activity className="animate-spin mr-2" size={20} /> Loading analysis…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-full text-gray-600 flex-col gap-3">
        <Target size={48} className="opacity-20" />
        <p>No hand data yet. Import hand history files to begin analysis.</p>
      </div>
    );
  }

  // --- Starting hand table ---
  const topHands = [...(data.startingHands || [])].sort((a, b) => b.total_net - a.total_net);
  const bestHands = topHands.slice(0, 10);
  const worstHands = [...topHands].reverse().slice(0, 10);
  const shownHands = handView === 'best' ? bestHands : worstHands;

  // --- Action frequency grouped by street ---
  const streetMap: Record<string, Record<string, number>> = {};
  for (const row of data.actionFreq || []) {
    if (!streetMap[row.street]) streetMap[row.street] = {};
    streetMap[row.street][row.action_type] = row.cnt;
  }
  const streetChartData = STREET_ORDER.filter(s => streetMap[s]).map(street => {
    const actions = streetMap[street];
    const total = Object.values(actions).reduce((a, b) => a + b, 0);
    const entry: Record<string, any> = { street };
    for (const [act, cnt] of Object.entries(actions)) {
      entry[act] = total > 0 ? Math.round((cnt / total) * 100) : 0;
    }
    return entry;
  });
  const actionTypes = ['fold', 'check', 'call', 'bet', 'raise', 'allin'];

  // --- P&L by game type ---
  const gameTypeData = (data.byGameType || []).map((g: any) => ({
    name: g.game_type,
    net: g.total_net / 100,
    hands: g.hands,
  }));

  // --- P&L by stakes ---
  const stakesData = (data.byStakes || []).slice(0, 8).map((s: any) => ({
    name: s.stakes,
    net: s.total_net / 100,
    hands: s.hands,
  }));

  // --- Pot size analysis ---
  const potData = (data.potAnalysis || []).map((p: any) => ({
    name: p.pot_category,
    winRate: p.hands > 0 ? Math.round((p.wins / p.hands) * 100) : 0,
    hands: p.hands,
    avgNet: p.avg_net_dollars,
  }));

  // --- Day of week ---
  const rawDays: Record<string, any> = {};
  for (const d of data.byDayOfWeek || []) rawDays[d.day] = d;
  const dayData = DAY_ORDER.map(day => ({
    day,
    net: rawDays[day] ? rawDays[day].total_net / 100 : 0,
    hands: rawDays[day]?.hands || 0,
  }));

  return (
    <div className="p-6 h-full overflow-y-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Target size={24} className="text-emerald-400" /> Gameplay Analysis
        </h2>
        <button onClick={load} className="text-gray-400 hover:text-white flex items-center gap-1 text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* ── Action Frequency by Street ── */}
      <section className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-sm font-bold text-gray-400 mb-3 flex items-center gap-2">
          <Activity size={14} /> Hero Action Frequency by Street (%)
        </h3>
        {streetChartData.length === 0 ? (
          <p className="text-gray-600 text-sm">No action data — import hands with hero tracking enabled.</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={streetChartData} stackOffset="expand">
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="street" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} tickFormatter={v => `${v}%`} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }}
                formatter={(v: number, name: string) => [`${v}%`, name]}
              />
              {actionTypes.map(act => (
                <Bar key={act} dataKey={act} stackId="a" fill={ACTION_COLORS[act] || '#6b7280'} name={act} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
        {/* Legend */}
        <div className="flex flex-wrap gap-3 mt-2">
          {actionTypes.map(a => (
            <span key={a} className="flex items-center gap-1 text-xs text-gray-400">
              <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: ACTION_COLORS[a] }} />
              {a}
            </span>
          ))}
        </div>
      </section>

      {/* ── Starting Hand Performance ── */}
      <section className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-gray-400 flex items-center gap-2">
            <Layers size={14} /> Starting Hand Performance
          </h3>
          <div className="flex gap-2">
            <button onClick={() => setHandView('best')}
              className={`text-xs px-3 py-1 rounded ${handView === 'best' ? 'bg-green-700 text-green-200' : 'bg-gray-700 text-gray-400'}`}>
              Best 10
            </button>
            <button onClick={() => setHandView('worst')}
              className={`text-xs px-3 py-1 rounded ${handView === 'worst' ? 'bg-red-800 text-red-200' : 'bg-gray-700 text-gray-400'}`}>
              Worst 10
            </button>
          </div>
        </div>
        {shownHands.length === 0 ? (
          <p className="text-gray-600 text-sm">Not enough data — need at least 2 hands per hole card combo.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-gray-700">
                  <th className="text-left py-2">Cards</th>
                  <th className="text-right py-2">Hands</th>
                  <th className="text-right py-2">Win%</th>
                  <th className="text-right py-2">Avg Result</th>
                  <th className="text-right py-2">Total P&L</th>
                </tr>
              </thead>
              <tbody>
                {shownHands.map((h: any, i: number) => {
                  const winPct = h.hands_played > 0 ? ((h.wins / h.hands_played) * 100).toFixed(0) : '0';
                  const avgNet = h.avg_net / 100;
                  const totalNet = h.total_net / 100;
                  return (
                    <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-750">
                      <td className="py-2 font-mono font-bold text-white">{h.hero_cards?.replace(',', ' ')}</td>
                      <td className="py-2 text-right text-gray-400">{h.hands_played}</td>
                      <td className="py-2 text-right text-gray-300">{winPct}%</td>
                      <td className={`py-2 text-right font-medium ${avgNet >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {avgNet >= 0 ? '+' : ''}{avgNet.toFixed(2)}
                      </td>
                      <td className={`py-2 text-right font-bold ${totalNet >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {totalNet >= 0 ? '+$' : '-$'}{Math.abs(totalNet).toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── P&L by Game Type + Stakes ── */}
      <div className="grid grid-cols-2 gap-4">
        <section className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3 flex items-center gap-2">
            <TrendingUp size={14} /> P&L by Game Type
          </h3>
          {gameTypeData.length === 0 ? (
            <p className="text-gray-600 text-sm">No data</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={gameTypeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} tickFormatter={v => `$${v}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }}
                  formatter={(v: number) => [`$${v.toFixed(2)}`, 'Net P&L']}
                />
                <Bar dataKey="net" radius={[4, 4, 0, 0]} name="Net P&L">
                  {gameTypeData.map((entry: any, i: number) => (
                    <Cell key={i} fill={entry.net >= 0 ? '#10b981' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>

        <section className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3 flex items-center gap-2">
            <TrendingDown size={14} /> P&L by Stakes
          </h3>
          {stakesData.length === 0 ? (
            <p className="text-gray-600 text-sm">No data</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={stakesData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#6b7280" fontSize={10} tickFormatter={v => `$${v}`} />
                <YAxis type="category" dataKey="name" stroke="#6b7280" fontSize={10} width={55} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }}
                  formatter={(v: number) => [`$${v.toFixed(2)}`, 'Net P&L']}
                />
                <Bar dataKey="net" radius={[0, 4, 4, 0]} name="Net P&L">
                  {stakesData.map((entry: any, i: number) => (
                    <Cell key={i} fill={entry.net >= 0 ? '#3b82f6' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      {/* ── Pot Size Win Rate + Day of Week ── */}
      <div className="grid grid-cols-2 gap-4">
        <section className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">Win Rate by Pot Size</h3>
          {potData.length === 0 ? (
            <p className="text-gray-600 text-sm">No data</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={potData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={9} angle={-15} textAnchor="end" height={50} />
                <YAxis stroke="#6b7280" fontSize={11} tickFormatter={v => `${v}%`} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }}
                  formatter={(v: number, name: string) => [name === 'winRate' ? `${v}%` : v, name === 'winRate' ? 'Win Rate' : 'Hands']}
                />
                <Bar dataKey="winRate" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="winRate" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>

        <section className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">P&L by Day of Week</h3>
          {dayData.every(d => d.hands === 0) ? (
            <p className="text-gray-600 text-sm">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={dayData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="day" stroke="#6b7280" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} tickFormatter={v => `$${v}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }}
                  formatter={(v: number) => [`$${v.toFixed(2)}`, 'Net P&L']}
                />
                <Bar dataKey="net" radius={[4, 4, 0, 0]} name="net">
                  {dayData.map((entry, i) => (
                    <Cell key={i} fill={entry.net >= 0 ? '#10b981' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>

      {/* ── Pot Size Details Table ── */}
      {potData.length > 0 && (
        <section className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">Pot Size Breakdown</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs border-b border-gray-700">
                <th className="text-left py-2">Category</th>
                <th className="text-right py-2">Hands</th>
                <th className="text-right py-2">Win Rate</th>
                <th className="text-right py-2">Avg Net</th>
              </tr>
            </thead>
            <tbody>
              {potData.map((p: any, i: number) => (
                <tr key={i} className="border-b border-gray-700/50">
                  <td className="py-2 text-gray-300">{p.name}</td>
                  <td className="py-2 text-right text-gray-400">{p.hands}</td>
                  <td className={`py-2 text-right font-medium ${p.winRate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                    {p.winRate}%
                  </td>
                  <td className={`py-2 text-right font-bold ${p.avgNet >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {p.avgNet >= 0 ? '+$' : '-$'}{Math.abs(p.avgNet || 0).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
