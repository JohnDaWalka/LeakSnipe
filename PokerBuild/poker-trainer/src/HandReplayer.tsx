import { useState, useEffect } from 'react';
import { Play, Pause, SkipBack, SkipForward, ChevronRight, ChevronLeft } from 'lucide-react';

// Types for our Replayer
export interface Player {
  name: string;
  seat: number; // 0-8
  chips: number;
  cards?: string[]; // e.g. ["Ah", "Kd"]
  isDealer?: boolean;
  isActive?: boolean; // In the hand
  currentBet?: number; // Current bet in front of player
}

export interface GameAction {
  playerIndex: number; // seat index
  type: 'post' | 'fold' | 'check' | 'call' | 'bet' | 'raise' | 'win';
  amount?: number;
  street?: 'Preflop' | 'Flop' | 'Turn' | 'River' | 'Showdown';
  board?: string[]; // Board cards revealed at this step
}

export interface HandData {
  id: string;
  site: string;
  blinds: string;
  players: Player[];
  actions: GameAction[];
}

// Mock Data for testing the UI
const MOCK_HAND: HandData = {
  id: "123456789",
  site: "CoinPoker",
  blinds: "0.50/1.00",
  players: [
    { name: "Hero", seat: 0, chips: 100, cards: ["As", "Ks"], isActive: true },
    { name: "Villain1", seat: 1, chips: 150, isActive: true },
    { name: "Villain2", seat: 2, chips: 80, isDealer: true, isActive: true },
    { name: "Villain3", seat: 3, chips: 200, isActive: true },
    { name: "Villain4", seat: 4, chips: 120, isActive: true },
    { name: "Villain5", seat: 5, chips: 90, isActive: true },
  ],
  actions: [
    { playerIndex: 0, type: 'post', amount: 0.5 },
    { playerIndex: 1, type: 'post', amount: 1.0 },
    { playerIndex: 2, type: 'fold' },
    { playerIndex: 3, type: 'fold' },
    { playerIndex: 4, type: 'raise', amount: 3.0 },
    { playerIndex: 5, type: 'fold' },
    { playerIndex: 0, type: 'call', amount: 2.5 },
    { playerIndex: 1, type: 'fold' },
    { playerIndex: -1, type: 'check', street: 'Flop', board: ['Th', 'Jc', '2d'] }, // -1 for system/dealer actions
    { playerIndex: 0, type: 'check' },
    { playerIndex: 4, type: 'bet', amount: 4.0 },
    { playerIndex: 0, type: 'call', amount: 4.0 },
    { playerIndex: -1, type: 'check', street: 'Turn', board: ['Th', 'Jc', '2d', 'Qd'] },
    { playerIndex: 0, type: 'check' },
    { playerIndex: 4, type: 'check' },
    { playerIndex: -1, type: 'check', street: 'River', board: ['Th', 'Jc', '2d', 'Qd', '9s'] },
    { playerIndex: 0, type: 'bet', amount: 15.0 },
    { playerIndex: 4, type: 'call', amount: 15.0 },
    { playerIndex: 0, type: 'win', amount: 45.0 }
  ]
};

export default function HandReplayer({ hand = MOCK_HAND }: { hand?: HandData }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Derived state based on currentStep
  const currentAction = hand.actions[currentStep];
  const board = hand.actions.slice(0, currentStep + 1).reduce((acc, action) => action.board || acc, [] as string[]);
  const pot = hand.actions.slice(0, currentStep + 1).reduce((acc, action) => acc + (action.amount || 0), 0);

  // Helper to calculate current chips/bets for each player at this step
  const playersState = hand.players.map(p => ({ ...p, currentBet: 0 }));
  
  // This is a naive replay logic, real logic needs to track streets to clear 'currentBet'
  // For now, simpler visualization
  hand.actions.slice(0, currentStep + 1).forEach(action => {
      if (action.playerIndex >= 0 && action.amount) {
          playersState[action.playerIndex].chips -= action.amount; // Visual only, assuming initial stacks
          playersState[action.playerIndex].currentBet = (playersState[action.playerIndex].currentBet || 0) + action.amount;
      }
      // If street changed, clear bets (simplified)
      if (action.board) { 
         playersState.forEach(p => p.currentBet = 0);
      }
  });

  const nextStep = () => {
    if (currentStep < hand.actions.length - 1) setCurrentStep(s => s + 1);
    else setIsPlaying(false);
  };

  const prevStep = () => {
    if (currentStep > 0) setCurrentStep(s => s - 1);
  };

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(nextStep, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentStep]);

  return (
    <div className="flex flex-col items-center bg-gray-900 text-white p-4 rounded-lg w-full max-w-4xl mx-auto h-[600px]">
      <div className="flex justify-between w-full mb-4">
        <div>
            <h2 className="text-xl font-bold">{hand.site} - {hand.blinds}</h2>
            <p className="text-gray-400 text-sm">Hand #{hand.id}</p>
        </div>
        <div className="text-right">
             <div className="text-2xl font-bold text-green-400">Pot: ${pot.toFixed(2)}</div>
             <div className="text-sm text-gray-400">Step {currentStep + 1}/{hand.actions.length}</div>
        </div>
      </div>

      {/* Poker Table Visualization */}
      <div className="relative w-[600px] h-[350px] bg-green-800 rounded-[150px] border-8 border-gray-700 shadow-2xl flex items-center justify-center my-6">
        
        {/* Board Cards */}
        <div className="flex gap-2 p-4 bg-black/20 rounded-lg">
            {board.length === 0 && <span className="text-white/30 text-sm">Wait for Flop...</span>}
            {board.map((card, i) => (
                <div key={i} className="bg-white w-10 h-14 rounded shadow flex items-center justify-center text-black font-bold border border-gray-400">
                    {card}
                </div>
            ))}
        </div>

        {/* Players */}
        {playersState.map((player, i) => {
            // Simple circular positioning logic
            // const angle = (i / playersState.length) * 2 * Math.PI + Math.PI / 2;
            // const radiusX = 320; // Horizontal radius
            // const radiusY = 190; // Vertical radius
            // const x = Math.cos(angle) * radiusX; // No offset needed if centered in container style
            // const y = Math.sin(angle) * radiusY;

            // Manual adjustments for seats 0-5 for better visual layout if needed
            // But let's use absolute positioning relative to center
            
            // Map 6 max to specific relative positions (approximate)
            const positions = [
                { top: '85%', left: '50%' }, // Hero (Seat 0) bottom center
                { top: '60%', left: '10%' },
                { top: '20%', left: '20%' },
                { top: '10%', left: '50%' },
                { top: '20%', left: '80%' },
                { top: '60%', left: '90%' },
            ];
            
            const pos = positions[i] || { top: '50%', left: '50%' };
            const isActing = currentAction && currentAction.playerIndex === i;

            return (
                <div 
                    key={i} 
                    className={`absolute w-24 p-2 rounded-lg text-center transform -translate-x-1/2 -translate-y-1/2 transition-colors duration-300
                        ${isActing ? 'bg-yellow-600 border-2 border-yellow-300' : 'bg-gray-800 border-2 border-gray-600'}
                    `}
                    style={{ ...pos }}
                >
                    <div className="text-xs font-bold truncate">{player.name}</div>
                    <div className="text-xs text-green-400">${player.chips.toFixed(2)}</div>
                    {player.cards && (
                        <div className="flex justify-center -mt-1 scale-75">
                           <div className="bg-white w-6 h-8 border border-gray-400 mr-1"></div>
                           <div className="bg-white w-6 h-8 border border-gray-400"></div>
                        </div>
                    )}
                    {player.isDealer && <div className="absolute -top-3 -right-3 w-6 h-6 bg-white text-black rounded-full flex items-center justify-center font-bold text-xs border border-gray-400">D</div>}
                    
                    {/* Current Bet Bubble */}
                    {(player.currentBet || 0) > 0 && (
                        <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 bg-black/60 px-2 py-0.5 rounded-full text-xs text-yellow-300">
                            ${player.currentBet}
                        </div>
                    )}
                </div>
            )
        })}
      </div>

      {/* Controls */}
      <div className="w-full flex items-center justify-center gap-4 mt-4 p-4 bg-gray-800 rounded-lg">
          <button onClick={() => setCurrentStep(0)} className="p-2 hover:bg-gray-700 rounded"><SkipBack size={20} /></button>
          <button onClick={prevStep} className="p-2 hover:bg-gray-700 rounded"><ChevronLeft size={20} /></button>
          
          <button 
            onClick={() => setIsPlaying(!isPlaying)} 
            className="w-12 h-12 flex items-center justify-center bg-blue-600 hover:bg-blue-500 rounded-full shadow-lg"
          >
              {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-1" />}
          </button>

          <button onClick={nextStep} className="p-2 hover:bg-gray-700 rounded"><ChevronRight size={20} /></button>
          <button onClick={() => setCurrentStep(hand.actions.length - 1)} className="p-2 hover:bg-gray-700 rounded"><SkipForward size={20} /></button>
      </div>

      {/* Action Text Log */}
      <div className="mt-4 w-full h-24 overflow-y-auto bg-black/40 p-2 rounded text-sm text-gray-300 font-mono">
           {currentAction ? (
               <div className="text-yellow-400">
                   {currentAction.street ? `--- ${currentAction.street} ---` : ''}
                   {currentAction.playerIndex >= 0 && `${hand.players[currentAction.playerIndex].name} `}
                   {currentAction.type.toUpperCase()} 
                   {currentAction.amount ? ` $${currentAction.amount}` : ''}
               </div>
           ) : 'Ready'}
      </div>

    </div>
  );
}
