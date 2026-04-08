'use client';
import Sidebar from "@/components/Sidebar";
import MainTerminal from "@/components/MainTerminal";
import { useState } from "react";

import ComparisonTerminal from "@/components/ComparisonTerminal";

export default function Home() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [currentView, setCurrentView] = useState('live');

  const handleAnalysisComplete = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="terminal-main">
      <Sidebar 
        onSelectTicker={(t) => { setSelectedTicker(t); setCurrentView('live'); }} 
        refreshTrigger={refreshTrigger}
        currentView={currentView}
        onViewChange={setCurrentView}
      />
      {currentView === 'live' ? (
        <MainTerminal 
          forceTicker={selectedTicker} 
          onAnalysisComplete={handleAnalysisComplete}
        />
      ) : (
        <ComparisonTerminal />
      )}
    </div>
  );
}
