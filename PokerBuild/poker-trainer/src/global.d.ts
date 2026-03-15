export {};

declare global {
  interface Window {
    ipc: {
      on: (channel: string, callback: (event: any, ...args: any[]) => void) => void;
      off: (channel: string, callback: (event: any, ...args: any[]) => void) => void;
    };
    pokerAPI: {
      // Live events
      onNewHand: (callback: (data: { site: string; raw: string }) => void) => () => void;
      onNewParsedHand: (callback: (data: any) => void) => () => void;
      onAppLog: (callback: (data: { msg: string; type: string }) => void) => () => void;
      // Database
      getHands: (opts?: { limit?: number; offset?: number; gameType?: string; site?: string }) => Promise<any[]>;
      getHandById: (id: string) => Promise<{ hand: any; actions: any[] } | null>;
      getSessions: (opts?: { limit?: number }) => Promise<any[]>;
      getSessionHands: (sessionId: string) => Promise<any[]>;
      getStats: () => Promise<{ totalHands: number; totalWon: number; gameTypes: any[]; recentResults: any[] } | null>;
      importParsedHands: (hands: any[]) => Promise<{ imported: number }>;
      // Therapy Rex
      analyzeSession: (sessionId: string) => Promise<any>;
      analyzeRecentHands: (count?: number) => Promise<any>;
      // Cloud Sync
      getCloudTargets: () => Promise<any[]>;
      addCloudTarget: (target: any) => Promise<any>;
      updateCloudTarget: (id: string, updates: any) => Promise<void>;
      removeCloudTarget: (id: string) => Promise<void>;
      detectCloudFolders: () => Promise<any[]>;
      // Parser
      parseHandText: (text: string, site: string) => Promise<any[]>;
      importFile: () => Promise<any[]>;
      // App
      getDriveHudPath: () => Promise<string>;
      getVersion: () => Promise<string>;
      getHeroName: () => Promise<string>;
      setHeroName: (name: string) => Promise<boolean>;
      // Hand History Paths (multi-client)
      getHHClients: () => Promise<{ name: string; site: string; paths: { path: string; exists: boolean }[] }[]>;
      getActiveHHPaths: () => Promise<{ path: string; site: string }[]>;
      addCustomHHPath: (p: string, site: string) => Promise<{ path: string; site: string }[]>;
      removeCustomHHPath: (p: string) => Promise<{ path: string; site: string }[]>;
      browseFolder: () => Promise<string | null>;
      // Leak Detection & Stats
      getLeakStats: (opts?: { limit?: number }) => Promise<any>;
      getTiltFlags: (opts?: { limit?: number }) => Promise<any[]>;
      getLeaks: (opts?: { limit?: number }) => Promise<any[]>;
      getSummaries: (opts?: { period?: string; limit?: number }) => Promise<any[]>;
      // Gameplay Analysis
      getGameplayAnalysis: () => Promise<{
        startingHands: any[];
        actionFreq: any[];
        byGameType: any[];
        byStakes: any[];
        potAnalysis: any[];
        byDayOfWeek: any[];
      } | null>;
      // Hand Tags
      addTag: (handId: string, tag: string) => Promise<boolean>;
      removeTag: (handId: string, tag: string) => Promise<boolean>;
      getTagsForHand: (handId: string) => Promise<string[]>;
      getAllTags: () => Promise<string[]>;
      getHandsByTag: (tag: string) => Promise<any[]>;
      // Backup
      runBackup: () => Promise<{ success: boolean; files: string[] }>;
      getBackups: () => Promise<{ name: string; date: string; sizeMB: number }[]>;
      getBackupDir: () => Promise<string>;
    };
  }
}
