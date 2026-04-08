'use client';
import React, { useState, useEffect } from 'react';

const Sidebar = ({ onSelectTicker, refreshTrigger, currentView, onViewChange }: { 
    onSelectTicker: (ticker: string) => void, 
    refreshTrigger?: number, 
    currentView: string,
    onViewChange: (view: string) => void
}) => {
    const [history, setHistory] = useState<any[]>([]);
    const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    useEffect(() => {
        // ... fetchHistory remains same ...
    }, [refreshTrigger]);

    return (
        <aside className="terminal-sidebar">
            <div style={{ padding: '24px 16px', borderBottom: '1px solid var(--border)' }}>
                <h3 className="grid-label" style={{ marginBottom: '12px' }}>Workspace</h3>
                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <button 
                        className={`sidebar-btn ${currentView === 'live' ? 'sidebar-btn-active' : ''}`}
                        onClick={() => onViewChange('live')}
                    >
                        Live Analysis
                    </button>
                    <button 
                        className={`sidebar-btn ${currentView === 'compare' ? 'sidebar-btn-active' : ''}`}
                        onClick={() => onViewChange('compare')}
                    >
                        ⚔️ vs COMPARE
                    </button>
                    <button className="sidebar-btn font-muted" disabled>History</button>
                </nav>
            </div>
            
            <div style={{ flex: 1, padding: '24px 16px', overflowY: 'auto' }}>
                <h3 className="grid-label" style={{ marginBottom: '12px' }}>Analysis History</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {history.length === 0 && (
                        <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>No previous analyses.</div>
                    )}
                    {history.map((item, i) => (
                        <div key={i} className="history-item" onClick={() => onSelectTicker(item.ticker)}>
                            <div className="history-ticker">{item.ticker}</div>
                            <div className="history-name">{item.name}</div>
                            <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.2)', marginTop: '4px' }}>
                                {item.archetype}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <style jsx>{`
                .sidebar-btn {
                    background: transparent;
                    border: none;
                    color: var(--text-muted);
                    text-align: left;
                    padding: 10px 12px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    border-radius: 4px;
                    transition: all 0.2s;
                }
                .sidebar-btn:hover {
                    background: rgba(255, 255, 255, 0.05);
                    color: var(--foreground);
                }
                .sidebar-btn-active {
                    background: rgba(14, 165, 233, 0.1);
                    color: var(--primary);
                }
                .history-item {
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.02);
                    border: 1px solid var(--border);
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .history-item:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-color: var(--secondary);
                }
                .history-ticker {
                    font-family: var(--font-mono);
                    font-weight: 700;
                    font-size: 13px;
                    color: var(--primary);
                }
                .history-name {
                    font-size: 11px;
                    color: var(--text-muted);
                }
            `}</style>
        </aside>
    );
};

export default Sidebar;
