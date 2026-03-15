import { useState, useEffect } from 'react';
import { Cloud, CheckCircle, XCircle, Plus, Trash2, FolderOpen, RefreshCw } from 'lucide-react';

interface SyncTarget {
  id: string;
  name: string;
  type: string;
  basePath: string;
  enabled: boolean;
  lastSync?: string;
  fileCount?: number;
}

export default function CloudSync() {
  const [targets, setTargets] = useState<SyncTarget[]>([]);
  const [newPath, setNewPath] = useState('');
  const [newName, setNewName] = useState('');

  useEffect(() => { loadTargets(); }, []);

  async function loadTargets() {
    const t = await window.pokerAPI.getCloudTargets();
    setTargets(t);
  }

  async function toggleTarget(id: string, enabled: boolean) {
    await window.pokerAPI.updateCloudTarget(id, { enabled });
    loadTargets();
  }

  async function removeTarget(id: string) {
    await window.pokerAPI.removeCloudTarget(id);
    loadTargets();
  }

  async function addNetworkPath() {
    if (!newPath.trim()) return;
    await window.pokerAPI.addCloudTarget({
      name: newName || `Network: ${newPath}`,
      type: 'network',
      basePath: newPath.trim(),
      enabled: true
    });
    setNewPath('');
    setNewName('');
    loadTargets();
  }

  async function detectFolders() {
    const detected = await window.pokerAPI.detectCloudFolders();
    if (detected.length === 0) {
      alert('No new cloud folders detected');
    }
    loadTargets();
  }

  return (
    <div className="p-6 h-full overflow-y-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Cloud className="text-blue-400" size={28} />
            Cloud & Network Sync
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Hand histories are synced to Google Drive (maurofanellijr@gmail.com), OneDrive, and network locations
          </p>
        </div>
        <button onClick={detectFolders}
          className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded text-sm">
          <RefreshCw size={14} /> Detect Folders
        </button>
      </div>

      {/* Current Sync Targets */}
      <div className="space-y-3">
        {targets.map(t => (
          <div key={t.id} className="bg-gray-800 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-3 h-3 rounded-full ${t.enabled ? 'bg-green-400' : 'bg-gray-600'}`} />
              <div>
                <div className="text-white font-medium">{t.name}</div>
                <div className="text-gray-500 text-xs font-mono mt-1">{t.basePath}</div>
                {t.lastSync && (
                  <div className="text-gray-600 text-xs mt-1">
                    Last sync: {new Date(t.lastSync).toLocaleString()} • {t.fileCount || 0} files
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-1 rounded ${
                t.type === 'google-drive' ? 'bg-green-900/30 text-green-400' :
                t.type === 'onedrive' ? 'bg-blue-900/30 text-blue-400' :
                'bg-gray-700 text-gray-400'
              }`}>
                {t.type === 'google-drive' ? '🔵 Google Drive' :
                 t.type === 'onedrive' ? '☁️ OneDrive' : '📁 Network'}
              </span>
              <button onClick={() => toggleTarget(t.id, !t.enabled)}
                className={`p-2 rounded ${t.enabled ? 'text-green-400 hover:bg-green-900/30' : 'text-gray-500 hover:bg-gray-700'}`}>
                {t.enabled ? <CheckCircle size={18} /> : <XCircle size={18} />}
              </button>
              {t.type === 'network' && (
                <button onClick={() => removeTarget(t.id)} className="p-2 text-red-400 hover:bg-red-900/30 rounded">
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          </div>
        ))}
        {targets.length === 0 && (
          <div className="bg-gray-800 rounded-lg p-8 text-center text-gray-500">
            No sync targets configured. Click "Detect Folders" or add a network path below.
          </div>
        )}
      </div>

      {/* Add Network Path */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <FolderOpen size={20} className="text-yellow-400" />
          Add Network Path
        </h3>
        <p className="text-gray-400 text-sm mb-4">
          Add a mapped drive or UNC path (e.g., \\server\share\poker or Z:\PokerBackup) for hand history backup.
        </p>
        <div className="flex gap-3">
          <input value={newName} onChange={e => setNewName(e.target.value)}
            placeholder="Label (optional)" className="bg-gray-900 text-white text-sm rounded px-3 py-2 w-48 border border-gray-700" />
          <input value={newPath} onChange={e => setNewPath(e.target.value)}
            placeholder="\\server\share\folder or D:\Backup\Poker" className="bg-gray-900 text-white text-sm rounded px-3 py-2 flex-1 border border-gray-700 font-mono" />
          <button onClick={addNetworkPath}
            className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm">
            <Plus size={14} /> Add
          </button>
        </div>
      </div>
    </div>
  );
}
