import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, History, PlayCircle, Brain, BarChart3, Cloud, Settings, Shield, Calendar, Target } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/hands', label: 'Hand History', icon: History },
  { path: '/replayer', label: 'Replayer', icon: PlayCircle },
  { path: '/rex', label: 'Rex Coach', icon: Brain },
  { path: '/stats', label: 'Statistics', icon: BarChart3 },
  { path: '/leaks', label: 'Leak Detector', icon: Shield },
  { path: '/analysis', label: 'Gameplay Analysis', icon: Target },
  { path: '/summaries', label: 'Summaries', icon: Calendar },
  { path: '/cloud', label: 'Cloud Sync', icon: Cloud },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col h-screen shrink-0">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold text-white">
          Poker<span className="text-blue-400">Therapist</span>
        </h1>
        <p className="text-xs text-gray-500 mt-1">Suite • DriveHUD2</p>
      </div>
      <nav className="flex-1 py-2 overflow-y-auto">
        {navItems.map(item => {
          const active = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                active
                  ? 'bg-blue-600/20 text-blue-400 border-r-2 border-blue-400'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-3 border-t border-gray-800 text-xs text-gray-600">
        Built for verbal session review with Rex
      </div>
    </aside>
  );
}
