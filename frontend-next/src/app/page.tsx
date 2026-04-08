'use client';
import Sidebar from "@/components/Sidebar";
import MainTerminal from "@/components/MainTerminal";
import { useState } from "react";

export default function Home() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleAnalysisComplete = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="terminal-main">
      <Sidebar 
        onSelectTicker={setSelectedTicker} 
        refreshTrigger={refreshTrigger} 
      />
      <MainTerminal 
        forceTicker={selectedTicker} 
        onAnalysisComplete={handleAnalysisComplete}
      />
    </div>
  );
}
