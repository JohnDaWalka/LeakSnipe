import { useState, useEffect } from 'react';
import { Search, Filter, FileUp, Tag, X } from 'lucide-react';

const QUICK_TAGS = ['bluff', 'hero-call', 'bad-beat', 'cooler', 'mistake', 'great-play', 'review', 'tilt-hand'];

export default function HandHistory() {
  const [hands, setHands] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [gameFilter, setGameFilter] = useState('');
  const [selectedHand, setSelectedHand] = useState<any>(null);
  const [handDetail, setHandDetail] = useState<any>(null);
  const [handTags, setHandTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  useEffect(() => {
    loadHands();
  }, [gameFilter]);

  async function loadHands() {
    const data = await window.pokerAPI.getHands({ limit: 200, gameType: gameFilter || undefined });
    setHands(data);
  }

  async function selectHand(id: string) {
    setSelectedHand(id);
    const [detail, tags] = await Promise.all([
      window.pokerAPI.getHandById(id),
      window.pokerAPI.getTagsForHand(id),
    ]);
    setHandDetail(detail);
    setHandTags(tags || []);
  }

  async function addTag(tag: string) {
    if (!selectedHand || !tag.trim()) return;
    await window.pokerAPI.addTag(selectedHand, tag.trim().toLowerCase());
    const tags = await window.pokerAPI.getTagsForHand(selectedHand);
    setHandTags(tags || []);
    setNewTag('');
  }

  async function removeTag(tag: string) {
    if (!selectedHand) return;
    await window.pokerAPI.removeTag(selectedHand, tag);
    const tags = await window.pokerAPI.getTagsForHand(selectedHand);
    setHandTags(tags || []);
  }

  async function importFiles() {
    const parsed = await window.pokerAPI.importFile();
    if (parsed && parsed.length > 0) {
      await window.pokerAPI.importParsedHands(parsed);
      loadHands();
    }
  }

  const filtered = hands.filter(h => {
    if (!search) return true;
    const s = search.toLowerCase();
    return h.id?.toLowerCase().includes(s) || h.game_type?.toLowerCase().includes(s) || h.stakes?.toLowerCase().includes(s);
  });

  return (
    <div className="flex h-full">
      {/* Hand List */}
      <div className="w-96 border-r border-gray-800 flex flex-col">
        <div className="p-4 space-y-3 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Hand History</h2>
            <button onClick={importFiles} className="flex items-center gap-1 text-sm bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded">
              <FileUp size={14} /> Import
            </button>
          </div>
          <div className="flex items-center gap-2 bg-gray-800 rounded px-3 py-2">
            <Search size={14} className="text-gray-500" />
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search hands…" className="bg-transparent text-sm text-white outline-none flex-1" />
          </div>
          <div className="flex gap-2">
            {['', 'NLHE', 'PLO', 'PLO5'].map(gt => (
              <button key={gt} onClick={() => setGameFilter(gt)}
                className={`text-xs px-2 py-1 rounded ${gameFilter === gt ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
                {gt || 'All'}
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {filtered.map(h => (
            <div key={h.id} onClick={() => selectHand(h.id)}
              className={`px-4 py-3 border-b border-gray-800 cursor-pointer hover:bg-gray-800 transition ${selectedHand === h.id ? 'bg-gray-800 border-l-2 border-blue-400' : ''}`}>
              <div className="flex justify-between text-sm">
                <span className="text-gray-300 font-medium">{h.game_type} {h.stakes}</span>
                <span className={h.net_amount >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {h.net_amount >= 0 ? '+' : ''}{(h.net_amount / 100).toFixed(2)}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                #{h.id} • {new Date(h.timestamp).toLocaleString()} • {h.won_pot ? '✓ Won' : '✗ Lost'}
              </div>
            </div>
          ))}
          {filtered.length === 0 && <p className="text-gray-600 text-sm p-4 text-center">No hands found. Import or play to populate.</p>}
        </div>
      </div>

      {/* Hand Detail */}
      <div className="flex-1 p-6 overflow-y-auto">
        {handDetail ? (
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-bold text-white">Hand #{handDetail.hand.id}</h3>
                <p className="text-gray-400 text-sm">{handDetail.hand.game_type} {handDetail.hand.stakes} — {handDetail.hand.site}</p>
              </div>
              <div className={`text-2xl font-bold ${handDetail.hand.net_amount >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {handDetail.hand.net_amount >= 0 ? '+' : ''}${(handDetail.hand.net_amount / 100).toFixed(2)}
              </div>
            </div>

            {/* Tags Section */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Tag size={14} className="text-blue-400" />
                <span className="text-sm font-medium text-gray-400">Tags</span>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {handTags.map(tag => (
                  <span key={tag} className="inline-flex items-center gap-1 bg-blue-600/30 text-blue-300 text-xs px-2 py-1 rounded">
                    {tag}
                    <button onClick={() => removeTag(tag)} className="hover:text-red-400"><X size={10} /></button>
                  </span>
                ))}
                {handTags.length === 0 && <span className="text-xs text-gray-600">No tags</span>}
              </div>
              <div className="flex gap-1.5 flex-wrap mb-2">
                {QUICK_TAGS.filter(t => !handTags.includes(t)).map(t => (
                  <button key={t} onClick={() => addTag(t)}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white">
                    + {t}
                  </button>
                ))}
              </div>
              <div className="flex gap-1">
                <input value={newTag} onChange={e => setNewTag(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addTag(newTag)}
                  placeholder="Custom tag…" className="bg-gray-900 text-xs text-white rounded px-2 py-1 flex-1 outline-none" />
                <button onClick={() => addTag(newTag)} className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-2 py-1 rounded">Add</button>
              </div>
            </div>

            {handDetail.hand.hero_cards && (
              <div className="bg-gray-800 rounded-lg p-4">
                <span className="text-gray-400 text-sm">Hero Cards:</span>
                <div className="flex gap-2 mt-2">
                  {handDetail.hand.hero_cards.split(',').map((c: string, i: number) => (
                    <div key={i} className="w-12 h-16 bg-white rounded shadow flex items-center justify-center text-black font-bold text-lg border border-gray-300">
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {handDetail.hand.board && (
              <div className="bg-gray-800 rounded-lg p-4">
                <span className="text-gray-400 text-sm">Board:</span>
                <div className="flex gap-2 mt-2">
                  {handDetail.hand.board.split(',').filter(Boolean).map((c: string, i: number) => (
                    <div key={i} className="w-12 h-16 bg-white rounded shadow flex items-center justify-center text-black font-bold text-lg border border-gray-300">
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-gray-800 rounded-lg p-4">
              <h4 className="text-sm font-bold text-gray-400 mb-3">Action Timeline</h4>
              <div className="space-y-1">
                {handDetail.actions.map((a: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500 w-16 text-xs">{a.street}</span>
                    <span className="text-gray-300 w-28 truncate">{a.player_name}</span>
                    <span className={`font-medium ${a.action_type === 'fold' ? 'text-gray-500' : a.action_type === 'raise' || a.action_type === 'bet' ? 'text-yellow-400' : 'text-blue-400'}`}>
                      {a.action_type.toUpperCase()}
                    </span>
                    {a.amount > 0 && <span className="text-gray-400">${(a.amount / 100).toFixed(2)}</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-600">
            <div className="text-center">
              <Filter size={48} className="mx-auto mb-4 opacity-30" />
              <p>Select a hand from the list to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
