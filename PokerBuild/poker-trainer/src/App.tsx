import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import HandHistory from './pages/HandHistory';
import HandReplayer from './HandReplayer';
import RexCoach from './pages/RexCoach';
import Statistics from './pages/Statistics';
import LeakDetector from './pages/LeakDetector';
import Summaries from './pages/Summaries';
import CloudSync from './pages/CloudSync';
import SettingsPage from './pages/Settings';
import GameplayAnalysis from './pages/GameplayAnalysis';
import Overlay from './Overlay';

function App() {
  return (
    <Routes>
      <Route path="/overlay" element={<Overlay />} />
      <Route path="*" element={
        <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-hidden">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/hands" element={<HandHistory />} />
              <Route path="/replayer" element={
                <div className="h-full bg-black flex items-center justify-center p-4">
                  <HandReplayer />
                </div>
              } />
              <Route path="/rex" element={<RexCoach />} />
              <Route path="/stats" element={<Statistics />} />
              <Route path="/leaks" element={<LeakDetector />} />
              <Route path="/analysis" element={<GameplayAnalysis />} />
              <Route path="/summaries" element={<Summaries />} />
              <Route path="/cloud" element={<CloudSync />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      } />
    </Routes>
  );
}

export default App;
