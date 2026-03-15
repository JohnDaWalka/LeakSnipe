import { useState, useEffect } from 'react';
import { Calendar, TrendingUp, BarChart3, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

type Period = 'daily' | 'weekly' | 'monthly';

export default function Summaries() {
  const [period, setPeriod] = useState<Period>('daily');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSummaries();
  }, [period]);

  async function loadSummaries() {
    setLoading(true);
    const result = await window.pokerAPI.getSummaries({ period, limit: 2000 });
    setData(result || []);
    setLoading(false);
  }

  // Build chart data with running total
  const chartData = data.map((d, i) => {
    const running = data.slice(0, i + 1).reduce((sum, x) => sum + (x.stats?.totalWon || 0), 0);
    return {
      label: d.period || d.label || `#${i + 1}`,
      pl: (d.stats?.totalWon || 0) / 100,
      cumPL: running / 100,
      hands: d.stats?.totalHands || d.handCount || 0,
      tiltFlags: d.tiltFlags?.length || 0,
    };
  });

  const totalPL = chartData.reduce((s, d) => s + d.pl, 0);
  const totalHands = chartData.reduce((s, d) => s + d.hands, 0);
  const totalTilts = chartData.reduce((s, d) => s + d.tiltFlags, 0);

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Calendar size={24} /> Summaries
        </h2>
        <div className="flex items-center gap-2">
          {(['daily', 'weekly', 'monthly'] as Period[]).map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              className={`text-sm px-3 py-1.5 rounded capitalize ${period === p ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:text-white'}`}>
              {p}
            </button>
          ))}
          <button onClick={loadSummaries} className="text-gray-400 hover:text-white ml-2"><RefreshCw size={16} /></button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-500">Loading…</div>
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center h-64 text-gray-600">No data yet. Play some hands!</div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-xs text-gray-500">Periods</div>
              <div className="text-2xl font-bold text-white">{data.length}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-xs text-gray-500">Total Hands</div>
              <div className="text-2xl font-bold text-white">{totalHands.toLocaleString()}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-xs text-gray-500">Total P&L</div>
              <div className={`text-2xl font-bold ${totalPL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {totalPL >= 0 ? '+' : ''}${totalPL.toFixed(2)}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-xs text-gray-500">Tilt Flags</div>
              <div className={`text-2xl font-bold ${totalTilts > 5 ? 'text-red-400' : totalTilts > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                {totalTilts}
              </div>
            </div>
          </div>

          {/* Cumulative P&L Chart */}
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2"><TrendingUp size={14} /> Cumulative P&L</h3>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px', color: '#fff' }} />
                <Area type="monotone" dataKey="cumPL" stroke="#60A5FA" fill="#60A5FA" fillOpacity={0.2} name="Cumulative $" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Per-period P&L bars */}
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2"><BarChart3 size={14} /> P&L per {period.slice(0, -2)}</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px', color: '#fff' }} />
                <Bar dataKey="pl" name="P&L $" fill="#60A5FA" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Period detail list */}
          <div className="space-y-2">
            {data.slice().reverse().map((d, i) => (
              <div key={i} className="bg-gray-800 rounded-lg px-4 py-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">{d.period || d.label}</div>
                  <div className="text-xs text-gray-500">{d.stats?.totalHands || d.handCount || 0} hands</div>
                </div>
                <div className="flex items-center gap-4">
                  {(d.tiltFlags?.length || 0) > 0 && (
                    <span className="text-xs text-yellow-400">⚠ {d.tiltFlags.length} tilt flags</span>
                  )}
                  <div className={`text-sm font-bold ${(d.stats?.totalWon || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {(d.stats?.totalWon || 0) >= 0 ? '+' : ''}${((d.stats?.totalWon || 0) / 100).toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
