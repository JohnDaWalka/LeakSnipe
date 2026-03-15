import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, FolderOpen, Database, Info, Plus, Trash2, CheckCircle, XCircle, Search } from 'lucide-react';

interface ClientInfo {
  name: string;
  site: string;
  paths: { path: string; exists: boolean }[];
}

interface ActivePath {
  path: string;
  site: string;
}

export default function SettingsPage() {
  const [driveHudPath, setDriveHudPath] = useState('');
  const [version, setVersion] = useState('');
  const [stats, setStats] = useState<any>(null);
  const [clients, setClients] = useState<ClientInfo[]>([]);
  const [activePaths, setActivePaths] = useState<ActivePath[]>([]);
  const [customSite, setCustomSite] = useState('CoinPoker');
  const [heroName, setHeroNameState] = useState('jdwalka');
  const [heroSaved, setHeroSaved] = useState(false);

  const loadData = () => {
    window.pokerAPI.getDriveHudPath().then(setDriveHudPath);
    window.pokerAPI.getVersion().then(setVersion);
    window.pokerAPI.getStats().then(setStats);
    window.pokerAPI.getHHClients().then(setClients);
    window.pokerAPI.getActiveHHPaths().then(setActivePaths);
    window.pokerAPI.getHeroName().then(name => setHeroNameState(name || 'jdwalka'));
  };

  useEffect(() => { loadData(); }, []);

  const handleSaveHeroName = async () => {
    await window.pokerAPI.setHeroName(heroName);
    setHeroSaved(true);
    setTimeout(() => setHeroSaved(false), 2000);
  };

  const handleAddCustomPath = async () => {
    const folder = await window.pokerAPI.browseFolder();
    if (folder) {
      await window.pokerAPI.addCustomHHPath(folder, customSite);
      loadData();
    }
  };

  const handleRemoveCustomPath = async (p: string) => {
    await window.pokerAPI.removeCustomHHPath(p);
    loadData();
  };

  return (
    <div className="p-6 h-full overflow-y-auto space-y-6">
      <h2 className="text-2xl font-bold text-white flex items-center gap-3">
        <SettingsIcon className="text-gray-400" size={28} />
        Settings
      </h2>

      {/* Hero Name */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          🎯 Hero (Your Player Name)
        </h3>
        <p className="text-gray-400 text-sm mb-3">
          Used to identify your actions across all hand histories. Must match your exact in-game username.
        </p>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={heroName}
            onChange={e => setHeroNameState(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSaveHeroName()}
            placeholder="Your poker username"
            className="flex-1 bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 text-sm font-mono focus:border-blue-500 outline-none"
          />
          <button
            onClick={handleSaveHeroName}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${heroSaved ? 'bg-green-700 text-green-200' : 'bg-blue-600 hover:bg-blue-500 text-white'}`}
          >
            {heroSaved ? '✓ Saved' : 'Save'}
          </button>
        </div>
        <p className="text-gray-600 text-xs mt-2">Current hero: <span className="text-blue-400 font-mono">{heroName}</span></p>
      </div>
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Search size={20} className="text-yellow-400" />
          Poker Client Hand History Paths
        </h3>
        <p className="text-gray-400 text-sm mb-4">
          The app auto-discovers hand history directories for your poker clients. Green paths are active and being watched.
        </p>

        {/* Auto-detected clients */}
        {clients.map(client => (
          <div key={client.name} className="mb-4">
            <h4 className="text-sm font-semibold text-white mb-2">{client.name} ({client.site})</h4>
            <div className="space-y-1 ml-4">
              {client.paths.map(p => (
                <div key={p.path} className="flex items-center gap-2 text-xs font-mono">
                  {p.exists
                    ? <CheckCircle size={14} className="text-green-400 shrink-0" />
                    : <XCircle size={14} className="text-gray-600 shrink-0" />}
                  <span className={p.exists ? 'text-green-300' : 'text-gray-600'}>{p.path}</span>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Active watch summary */}
        <div className="mt-4 bg-gray-900 rounded p-3">
          <div className="text-sm font-semibold text-white mb-2">Active Watched Paths ({activePaths.length})</div>
          {activePaths.length === 0 && (
            <p className="text-gray-500 text-xs">No paths are currently being watched. Add a custom path below.</p>
          )}
          {activePaths.map(a => (
            <div key={a.path} className="flex items-center justify-between text-xs font-mono py-1">
              <span className="text-green-300 truncate">[{a.site}] {a.path}</span>
              <button onClick={() => handleRemoveCustomPath(a.path)} className="text-red-400 hover:text-red-300 ml-2 shrink-0" title="Remove custom path">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        {/* Add custom path */}
        <div className="mt-4 flex items-center gap-2">
          <select value={customSite} onChange={e => setCustomSite(e.target.value)}
            className="bg-gray-900 border border-gray-700 text-white text-sm rounded px-2 py-1.5">
            <option value="CoinPoker">CoinPoker</option>
            <option value="BetACR">BetACR / ACR</option>
            <option value="DriveHUD2">DriveHUD2</option>
            <option value="PokerStars">PokerStars</option>
            <option value="Other">Other</option>
          </select>
          <button onClick={handleAddCustomPath}
            className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 text-white text-sm px-3 py-1.5 rounded">
            <Plus size={14} /> Add HH Folder
          </button>
        </div>
      </div>

      {/* DriveHUD2 Config */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <FolderOpen size={20} className="text-blue-400" />
          DriveHUD2 Integration
        </h3>
        <div className="space-y-3">
          <div>
            <label className="text-gray-400 text-sm block mb-1">Hand History Path (auto-detected)</label>
            <div className="bg-gray-900 text-gray-300 text-sm font-mono rounded px-3 py-2 border border-gray-700">
              {driveHudPath || 'Detecting…'}
            </div>
          </div>
          <p className="text-gray-500 text-xs">
            DriveHUD2 ProcessedData folder is monitored for new WinningPokerNetwork hand histories (Hold'em & Omaha).
          </p>
        </div>
      </div>

      {/* Database Info */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Database size={20} className="text-green-400" />
          Local Database
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-400 text-xs">Hands Stored</div>
            <div className="text-xl font-bold text-white">{stats?.totalHands || 0}</div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-400 text-xs">Game Types</div>
            <div className="text-xl font-bold text-white">{stats?.gameTypes?.length || 0}</div>
          </div>
          <div className="bg-gray-900 rounded p-3">
            <div className="text-gray-400 text-xs">Net Result</div>
            <div className={`text-xl font-bold ${(stats?.totalWon || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${((stats?.totalWon || 0) / 100).toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Info size={20} className="text-purple-400" />
          About
        </h3>
        <div className="space-y-2 text-sm text-gray-400">
          <p><strong>Poker Therapist Suite</strong> — Custom software for session review with Rex Poker Coach</p>
          <p>Version: {version || '1.0.0'}</p>
          <p>Platform: Windows 11 • Electron • React • SQLite</p>
          <p>Poker Clients: CoinPoker • BetACR (Americas Cardroom) • DriveHUD2</p>
          <p>Cloud Sync: Google Drive (maurofanellijr@gmail.com) + OneDrive + Network</p>
          <p className="text-gray-600 mt-4">Built by mfane • Designed for verbal poker session review</p>
        </div>
      </div>
    </div>
  );
}
