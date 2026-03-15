import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Activity, TrendingUp, TrendingDown, Layers } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [activeWindow, setActiveWindow] = useState<any>(null);
  const [logs, setLogs] = useState<{ msg: string; type: string; time: string }[]>([]);
  const [liveHands, setLiveHands] = useState<any[]>([]);

  useEffect(() => {
    window.pokerAPI.getStats().then(setStats);

    window.ipc.on('active-window-data', (_e, data) => setActiveWindow(data));

    const cleanupLog = window.pokerAPI.onAppLog((data) => {
      setLogs(prev => [{ ...data, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 30));
    });

    const cleanupHand = window.pokerAPI.onNewParsedHand((hands) => {
      setLiveHands(prev => [...hands, ...prev].slice(0, 50));
      window.pokerAPI.getStats().then(setStats);
    });

    return () => { cleanupLog(); cleanupHand(); };
  }, []);

  const chartData = stats?.recentResults
    ?.slice().reverse()
    .reduce((acc: any[], h: any, i: number) => {
      const prev = acc.length > 0 ? acc[acc.length - 1].cumulative : 0;
      acc.push({ hand: i + 1, result: h.net_amount / 100, cumulative: prev + h.net_amount / 100 });
      return acc;
    }, []) || [];

  const totalWon = (stats?.totalWon || 0) / 100;

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        {activeWindow && (
          <div className="flex items-center gap-2 bg-green-900/30 border border-green-700 text-green-400 px-3 py-1.5 rounded-full text-sm">
            <Activity size={14} className="animate-pulse" />
            <span>Tracking: {activeWindow.appName}</span>
          </div>
        )}
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Hands" value={stats?.totalHands || 0} icon={<Layers size={20} />} />
        <StatCard label="Net Result" value={`$${totalWon.toFixed(2)}`}
          icon={totalWon >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
          color={totalWon >= 0 ? 'text-green-400' : 'text-red-400'} />
        <StatCard label="Game Types" value={stats?.gameTypes?.map((g: any) => g.game_type).join(', ') || '—'} icon={<Layers size={20} />} />
        <StatCard label="Live Hands" value={liveHands.length} icon={<Activity size={20} />} />
      </div>

      {/* Win/Loss Chart */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-4">Cumulative Results (Last 200 Hands)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="hand" stroke="#6b7280" fontSize={12} />
            <YAxis stroke="#6b7280" fontSize={12} tickFormatter={(v: number) => `$${v}`} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
              labelStyle={{ color: '#9ca3af' }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, 'Cumulative']}
            />
            <Line type="monotone" dataKey="cumulative" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Hands + Logs */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
          <h3 className="text-sm font-bold text-gray-400 mb-2">Live Hand Feed</h3>
          {liveHands.length === 0 && <p className="text-gray-600 text-sm">Waiting for hands from DriveHUD2…</p>}
          {liveHands.slice(0, 15).map((h, i) => (
            <div key={i} className="flex justify-between text-xs py-1 border-b border-gray-700">
              <span className="text-gray-300">{h.gameType} {h.stakes}</span>
              <span className={h.heroNetAmount >= 0 ? 'text-green-400' : 'text-red-400'}>
                {h.heroNetAmount >= 0 ? '+' : ''}{h.heroNetAmount.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
        <div className="bg-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
          <h3 className="text-sm font-bold text-gray-400 mb-2">Application Logs</h3>
          {logs.map((log, i) => (
            <div key={i} className={`text-xs font-mono py-0.5 ${log.type === 'error' ? 'text-red-400' : 'text-green-400'}`}>
              <span className="text-gray-600">[{log.time}]</span> {log.msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon, color = 'text-white' }: { label: string; value: any; icon: React.ReactNode; color?: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{label}</span>
        <span className="text-gray-500">{icon}</span>
      </div>
      <div className={`text-xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
