import { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Statistics() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    window.pokerAPI.getStats().then(setStats);
  }, []);

  if (!stats) return <div className="flex items-center justify-center h-full text-gray-500">Loading statistics…</div>;

  const totalWon = (stats.totalWon || 0) / 100;

  // Cumulative chart
  const cumData = stats.recentResults?.slice().reverse().reduce((acc: any[], h: any, i: number) => {
    const prev = acc.length > 0 ? acc[acc.length - 1].cumulative : 0;
    acc.push({ hand: i + 1, result: h.net_amount / 100, cumulative: prev + h.net_amount / 100, type: h.game_type });
    return acc;
  }, []) || [];

  // Per-game-type breakdown
  const gameData = stats.gameTypes?.map((g: any) => ({ name: g.game_type, value: g.count })) || [];

  // Win/loss distribution
  const wins = stats.recentResults?.filter((h: any) => h.net_amount > 0).length || 0;
  const losses = stats.recentResults?.filter((h: any) => h.net_amount < 0).length || 0;
  const breakeven = stats.recentResults?.filter((h: any) => h.net_amount === 0).length || 0;
  const winLossData = [
    { name: 'Wins', value: wins }, { name: 'Losses', value: losses }, { name: 'Break-even', value: breakeven }
  ];

  // Result distribution histogram
  const buckets = new Map<string, number>();
  for (const h of stats.recentResults || []) {
    const amt = h.net_amount / 100;
    let bucket: string;
    if (amt <= -50) bucket = '<-$50';
    else if (amt <= -20) bucket = '-$50 to -$20';
    else if (amt <= -5) bucket = '-$20 to -$5';
    else if (amt < 5) bucket = '-$5 to $5';
    else if (amt < 20) bucket = '$5 to $20';
    else if (amt < 50) bucket = '$20 to $50';
    else bucket = '>$50';
    buckets.set(bucket, (buckets.get(bucket) || 0) + 1);
  }
  const histData = ['<-$50', '-$50 to -$20', '-$20 to -$5', '-$5 to $5', '$5 to $20', '$20 to $50', '>$50']
    .map(b => ({ range: b, count: buckets.get(b) || 0 }));

  return (
    <div className="p-6 h-full overflow-y-auto space-y-6">
      <h2 className="text-2xl font-bold text-white">Statistics</h2>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <Stat label="Total Hands" value={stats.totalHands} />
        <Stat label="Net P&L" value={`$${totalWon.toFixed(2)}`} color={totalWon >= 0 ? 'text-green-400' : 'text-red-400'} />
        <Stat label="Win Rate" value={stats.totalHands > 0 ? `${(wins / stats.recentResults.length * 100).toFixed(1)}%` : '—'} />
        <Stat label="Avg Result" value={stats.totalHands > 0 ? `$${(totalWon / stats.totalHands).toFixed(2)}` : '—'} />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Cumulative PnL */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">Cumulative P&L</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={cumData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hand" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={11} tickFormatter={v => `$${v}`} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }}
                formatter={(v: number) => [`$${v.toFixed(2)}`]} />
              <Line type="monotone" dataKey="cumulative" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Game Type Breakdown */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">Hands by Game Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={gameData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
                {gameData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Win/Loss Pie */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">Win/Loss Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={winLossData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                <Cell fill="#10b981" />
                <Cell fill="#ef4444" />
                <Cell fill="#6b7280" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Result Histogram */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-bold text-gray-400 mb-3">Result Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={histData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="range" stroke="#6b7280" fontSize={10} angle={-30} textAnchor="end" height={60} />
              <YAxis stroke="#6b7280" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px' }} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color = 'text-white' }: { label: string; value: any; color?: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-gray-400 text-sm mb-1">{label}</div>
      <div className={`text-xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
