import { useEffect, useState } from "react";
import { Eye } from "lucide-react";

export interface OverlayProps {
  title?: string;
}

export default function Overlay() {
  const [stats, setStats] = useState({
    handsPlayed: 0,
    vpip: 0,
    pfr: 0,
    lastAction: "Waiting for hand...",
    site: "Unknown"
  });

  useEffect(() => {
    // Listen for bounds/target updates if needed, though mostly main process handles position.
    // Listen for new hand data to update real-time stats
    
    // @ts-ignore
    const cleanup = window.pokerAPI?.onNewHand((data: any) => {
        setStats(prev => ({
            ...prev,
            handsPlayed: prev.handsPlayed + 1,
            lastAction: "Hand imported",
            site: data.site
        }));
    });

    return () => cleanup && cleanup();
  }, []);

  return (
    <div style={{ 
      width: '100vw', 
      height: '100vh', 
      background: 'rgba(0, 0, 0, 0)', // Fully transparent background
      overflow: 'hidden',
      pointerEvents: 'none' // Click-through
    }}>
      {/* HUD Panel - Positioned top left or custom */}
      <div style={{
        position: 'absolute',
        top: 40,
        left: 10,
        background: 'rgba(20, 20, 20, 0.85)',
        color: '#fff',
        padding: '8px',
        borderRadius: '8px',
        fontSize: '12px',
        border: '1px solid #444',
        pointerEvents: 'auto' // Make stats clickable if needed
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <Eye size={14} color="#4ade80" />
            <span style={{ fontWeight: 'bold' }}>{stats.site} Tracking</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div>
                <div style={{ color: '#aaa', fontSize: '10px' }}>Hands</div>
                <div>{stats.handsPlayed}</div>
            </div>
            <div>
                 <div style={{ color: '#aaa', fontSize: '10px' }}>VPIP / PFR</div>
                 <div>{stats.vpip}% / {stats.pfr}%</div>
            </div>
        </div>
        <div style={{ marginTop: '4px', fontSize: '10px', color: '#fbbf24' }}>
            {stats.lastAction}
        </div>
      </div>
    </div>
  );
}
