import { useState } from 'react';
import { Brain, RefreshCw, MessageCircle, AlertTriangle, CheckCircle, Flame } from 'lucide-react';

export default function RexCoach() {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [handCount, setHandCount] = useState(50);

  async function runAnalysis() {
    setLoading(true);
    try {
      const result = await window.pokerAPI.analyzeRecentHands(handCount);
      setAnalysis(result);
    } catch (e) {
      console.error('Rex analysis failed:', e);
    }
    setLoading(false);
  }

  const gradeColor: Record<string, string> = {
    A: 'text-green-400 bg-green-900/30 border-green-700',
    B: 'text-blue-400 bg-blue-900/30 border-blue-700',
    C: 'text-yellow-400 bg-yellow-900/30 border-yellow-700',
    D: 'text-red-400 bg-red-900/30 border-red-700',
  };

  return (
    <div className="p-6 h-full overflow-y-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Brain className="text-purple-400" size={28} />
            Rex Poker Coach
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Verbal session review prep — tilt detection, composure scoring & debrief talking points
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select value={handCount} onChange={e => setHandCount(Number(e.target.value))}
            className="bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700">
            <option value={25}>Last 25 hands</option>
            <option value={50}>Last 50 hands</option>
            <option value={100}>Last 100 hands</option>
            <option value={200}>Last 200 hands</option>
          </select>
          <button onClick={runAnalysis} disabled={loading}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded font-medium disabled:opacity-50">
            {loading ? <RefreshCw size={16} className="animate-spin" /> : <Brain size={16} />}
            {loading ? 'Analyzing…' : 'Analyze Session'}
          </button>
        </div>
      </div>

      {!analysis && !loading && (
        <div className="flex flex-col items-center justify-center h-96 text-gray-500">
          <Brain size={64} className="opacity-20 mb-4" />
          <p className="text-lg">Click "Analyze Session" to generate your Rex debrief</p>
          <p className="text-sm mt-2">Rex will review your recent hands and prepare talking points for your verbal review</p>
        </div>
      )}

      {analysis && (
        <div className="space-y-6">
          {/* Grade Banner */}
          <div className={`rounded-lg p-6 border ${gradeColor[analysis.overallGrade] || gradeColor.C}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-4xl font-black">{analysis.overallGrade}</div>
                <div className="text-sm mt-1 opacity-80">Session Grade</div>
              </div>
              <div className="text-right">
                <p className="text-sm opacity-90">{analysis.summary}</p>
              </div>
            </div>
          </div>

          {/* Talking Points for Rex Review */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <MessageCircle size={20} className="text-blue-400" />
              Talking Points for Rex
            </h3>
            <p className="text-gray-400 text-sm mb-4">
              Use these points when reviewing the session verbally with your Rex Poker Therapist/Coach:
            </p>
            <div className="space-y-3">
              {analysis.talkingPoints?.map((point: string, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-900 rounded-lg">
                  <span className="text-blue-400 font-bold text-sm mt-0.5">{i + 1}.</span>
                  <span className="text-gray-200 text-sm">{point}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Key Moments */}
          {analysis.keyMoments?.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Flame size={20} className="text-orange-400" />
                Key Moments (Tilt Events)
              </h3>
              <div className="space-y-2">
                {analysis.keyMoments.map((moment: string, i: number) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-red-900/20 border border-red-800/30 rounded">
                    <AlertTriangle size={16} className="text-red-400 shrink-0" />
                    <span className="text-sm text-gray-300">{moment}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Copy for Rex */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-2">📋 Quick Copy for Rex Session</h3>
            <p className="text-gray-400 text-sm mb-3">Copy this summary to share with your Rex coach:</p>
            <div className="bg-gray-900 rounded p-4 text-sm text-gray-300 font-mono whitespace-pre-wrap select-all">
              {`Session Debrief — ${new Date().toLocaleDateString()}\n\n${analysis.summary}\n\nTalking Points:\n${analysis.talkingPoints?.map((p: string, i: number) => `${i + 1}. ${p}`).join('\n')}\n\nKey Moments:\n${analysis.keyMoments?.join('\n') || 'None detected'}`}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
