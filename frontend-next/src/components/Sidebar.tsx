'use client';

import React, { useEffect, useState } from 'react';
import { safeFetch } from '@/utils/api';

type HistoryItem = {
    ticker: string;
    name: string;
    archetype: string;
    date?: string;
};

type SidebarProps = {
    onSelectTicker: (ticker: string) => void;
    refreshTrigger?: number;
    currentView: 'live' | 'compare' | 'intelligence';
    onViewChange: (view: 'live' | 'compare' | 'intelligence') => void;
};

const Sidebar = ({ onSelectTicker, refreshTrigger, currentView, onViewChange }: SidebarProps) => {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [historyError, setHistoryError] = useState<string | null>(null);
    
    // Direct link to backend to bypass Vercel proxy issues
    const BACKEND_PROD_URL = "https://ghouri112-financial-terminal-backend.hf.space";
    const BASE_URL = (typeof window !== 'undefined' && (window.location.hostname.includes('vercel.app') || window.location.hostname.includes('github.dev'))) 
        ? BACKEND_PROD_URL 
        : (typeof window !== 'undefined' ? window.location.origin : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7860')).replace(/\\n/g, '').trim();
    
    const API_KEY = (process.env.NEXT_PUBLIC_API_KEY || 'dev_default_key').replace(/\\n/g, '').trim();

    useEffect(() => {
        let isActive = true;
        const fetchHistory = async () => {
            setIsLoading(true);
            setHistoryError(null);
            try {
                const response = await safeFetch(`${BASE_URL}/api/history`, {
                    headers: {
                        'X-API-Key': API_KEY,
                    },
                });
                
                if (!response.success) {
                    throw new Error(response.error);
                }

                if (isActive) {
                    setHistory(Array.isArray(response.data) ? response.data : []);
                }
            } catch (err) {
                const message = err instanceof Error ? err.message : 'Failed to load history.';
                if (isActive) {
                    setHistoryError(message);
                    setHistory([]);
                }
            } finally {
                if (isActive) {
                    setIsLoading(false);
                }
            }
        };

        void fetchHistory();
        return () => {
            isActive = false;
        };
    }, [API_KEY, BASE_URL, refreshTrigger]);

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
                        className={`sidebar-btn ${currentView === 'intelligence' ? 'sidebar-btn-active' : ''}`}
                        onClick={() => onViewChange('intelligence')}
                    >
                        📊 Chart Intel
                    </button>
                    <button
                        className={`sidebar-btn ${currentView === 'compare' ? 'sidebar-btn-active' : ''}`}
                        onClick={() => onViewChange('compare')}
                    >
                        VS Compare
                    </button>
                </nav>
            </div>

            <div style={{ flex: 1, padding: '24px 16px', overflowY: 'auto' }}>
                <h3 className="grid-label" style={{ marginBottom: '12px' }}>Analysis History</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {isLoading && (
                        <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                            Loading history...
                        </div>
                    )}
                    {!isLoading && historyError && (
                        <div style={{ color: '#DC2626', fontSize: '11px' }}>
                            {historyError}
                        </div>
                    )}
                    {!isLoading && !historyError && history.length === 0 && (
                        <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>No previous analyses.</div>
                    )}
                    {history.map((item, index) => (
                        <button
                            key={`${item.ticker}-${index}`}
                            className="history-item"
                            onClick={() => {
                                onViewChange('live');
                                onSelectTicker(item.ticker);
                            }}
                        >
                            <div className="history-ticker">{item.ticker}</div>
                            <div className="history-name">{item.name}</div>
                            <div style={{ fontSize: '9px', color: 'rgba(15, 23, 42, 0.45)', marginTop: '4px' }}>
                                {item.archetype}
                            </div>
                        </button>
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
                    background: var(--bg-hover);
                    color: var(--foreground);
                }

                .sidebar-btn-active {
                    background: linear-gradient(135deg, #EFF6FF, #F5F3FF);
                    border: 1px solid #DBEAFE;
                    color: var(--primary);
                    font-weight: 600;
                }

                .history-item {
                    padding: 12px;
                    background: var(--bg-surface);
                    border: 1px solid var(--border);
                    cursor: pointer;
                    transition: all 0.2s;
                    text-align: left;
                }

                .history-item:hover {
                    background: var(--bg-hover);
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
                    margin-top: 2px;
                }
            `}</style>
        </aside>
    );
};

export default Sidebar;
