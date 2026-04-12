'use client';

import React, { useEffect, useState, useRef } from 'react';
import { safeFetch } from '@/utils/api';

declare global {
  interface Window {
    TradingView: any;
  }
}

interface SignalData {
  ticker: string;
  price_change: number;
  explanation: string;
  confidence: number;
  signals: any;
}

const ChartIntelligence = ({ ticker: initialTicker }: { ticker: string }) => {
    const [ticker, setTicker] = useState(initialTicker || 'AAPL');
    const [inputVal, setInputVal] = useState(initialTicker || 'AAPL');
    const [intelligence, setIntelligence] = useState<SignalData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Direct link to backend to bypass Vercel proxy issues
    const BACKEND_PROD_URL = "https://ghouri112-financial-terminal-backend.hf.space";
    const BASE_URL = (typeof window !== 'undefined' && (window.location.hostname.includes('vercel.app') || window.location.hostname.includes('github.dev'))) 
        ? BACKEND_PROD_URL 
        : (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:7860').replace(/\\n/g, '').trim();

    const [markers, setMarkers] = useState<any[]>([]);

    const fetchIntelligence = async (symbol: string) => {
        setIsLoading(true);
        setError(null);
        try {
            console.log(`[FETCH] Requesting AI Intelligence for ${symbol} from: ${BASE_URL}`);
            
            const intelRes = await safeFetch(`${BASE_URL}/api/explain-chart?ticker=${symbol}`);
            
            if (!intelRes.success) {
                throw new Error(intelRes.error);
            }

            const intelData = intelRes.data;
            
            // Also fetch markers safely
            const markersRes = await safeFetch(`${BASE_URL}/api/timeline-markers?ticker=${symbol}`);
            const markersData = markersRes.success ? markersRes.data : [];
            
            setIntelligence(intelData);
            setMarkers(Array.isArray(markersData) ? markersData : []);
        } catch (err: any) {
            console.error("[CHART_INTEL_ERROR]", err);
            setError(err.message || 'Unable to generate AI chart analysis');
        } finally {
            setIsLoading(false);
        }
    };

    const loadChart = (symbol: string, chartMarkers: any[]) => {
        if (window.TradingView && containerRef.current) {
            containerRef.current.innerHTML = ''; // Clear previous
            const child = document.createElement('div');
            child.id = `tv_chart_${Date.now()}`;
            child.style.height = '100%';
            containerRef.current.appendChild(child);

            // Construct markings/shapes for TradingView
            // Note: Standard widget has limited support for programmatic shapes without Advanced Charting Library
            // but we can use 'details' and 'calendar' to enrich the view.
            
            new window.TradingView.widget({
                "container_id": child.id,
                "autosize": true,
                "symbol": symbol.includes(':') ? symbol : `NASDAQ:${symbol}`,
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#0f172a",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "details": true,
                "hotlist": true,
                "calendar": true,
                "show_popup_button": true,
                "popup_width": "1000",
                "popup_height": "650",
            });
        }
    };

    useEffect(() => {
        fetchIntelligence(ticker);
    }, [ticker]);

    useEffect(() => {
        if (!isLoading) {
            loadChart(ticker, markers);
        }
    }, [isLoading, ticker, markers]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (inputVal.trim()) {
            setTicker(inputVal.trim().toUpperCase());
        }
    };

    const getConfidenceColor = (score: number) => {
        if (score > 0.7) return '#059669'; // Green
        if (score > 0.4) return '#d97706'; // Yellow
        return '#dc2626'; // Red
    };

    return (
        <div className="intelligence-container">
            {/* Header with Search */}
            <div className="intel-header">
                <form onSubmit={handleSearch} className="search-form">
                    <input 
                        type="text" 
                        value={inputVal} 
                        onChange={(e) => setInputVal(e.target.value)}
                        placeholder="Enter Ticker (e.g. NVDA)"
                        className="ticker-input"
                    />
                    <button type="submit" className="search-btn">ANALYZE CHART</button>
                </form>
            </div>

            {/* AI Explanation Box */}
            <section className="explanation-card">
                <div className="card-header">
                    <div className="title-row">
                        <span className="icon">🧠</span>
                        <h3>FORENSIC CHART SIGNALS: {ticker}</h3>
                        {intelligence && (
                            <span 
                                className="confidence-badge"
                                style={{ backgroundColor: getConfidenceColor(intelligence.confidence) }}
                            >
                                {(intelligence.confidence * 100).toFixed(0)}% CONFIDENT
                            </span>
                        )}
                    </div>
                </div>
                
                <div className="card-body">
                    {isLoading ? (
                        <div className="loading-text">Scanning for institutional patterns...</div>
                    ) : error ? (
                        <div className="error-text">⚠️ {error}</div>
                    ) : intelligence ? (
                        <p className="explanation-text">{intelligence.explanation}</p>
                    ) : (
                        <p className="explanation-text">Enter a ticker to begin forensic chart analysis.</p>
                    )}
                </div>
            </section>

            {/* TradingView Widget */}
            <div className="chart-wrapper">
                <div id="tv_chart_container" ref={containerRef} style={{ height: '550px' }} />
            </div>

            <style jsx>{`
                .intelligence-container {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    padding: 24px;
                    height: 100%;
                    overflow-y: auto;
                    background: var(--bg-surface);
                }
                .intel-header {
                    display: flex;
                    justify-content: flex-end;
                    margin-bottom: 8px;
                }
                .search-form {
                    display: flex;
                    gap: 0;
                }
                .ticker-input {
                    background: var(--bg-elevated);
                    border: 1px solid var(--border);
                    color: var(--text-primary);
                    padding: 8px 12px;
                    font-family: var(--font-mono);
                    font-size: 13px;
                    width: 200px;
                    outline: none;
                }
                .ticker-input:focus {
                    border-color: var(--primary);
                }
                .search-btn {
                    background: linear-gradient(135deg,#2563EB,#1D4ED8);
                    color: white;
                    border: none;
                    padding: 0 16px;
                    font-size: 11px;
                    font-weight: 700;
                    cursor: pointer;
                    text-transform: uppercase;
                }
                .search-btn:hover {
                    background: linear-gradient(135deg,#1D4ED8,#1E40AF);
                }
                .explanation-card {
                    background: var(--bg-surface);
                    border: 1px solid var(--border);
                    border-left: 4px solid var(--primary);
                    padding: 20px;
                    box-shadow: var(--shadow-sm);
                }
                .title-row {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 12px;
                }
                .title-row h3 {
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.05em;
                    color: var(--primary);
                    margin: 0;
                    text-transform: uppercase;
                }
                .confidence-badge {
                    font-size: 10px;
                    font-weight: 800;
                    color: white;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                .explanation-text {
                    font-size: 15px;
                    line-height: 1.6;
                    color: var(--text-primary);
                    margin: 0;
                }
                .loading-text {
                    color: var(--text-muted);
                    font-size: 13px;
                    font-style: italic;
                }
                .error-text {
                    color: #ef4444;
                    font-size: 13px;
                }
                .chart-wrapper {
                    flex: 1;
                    min-height: 550px;
                    border: 1px solid var(--border);
                    background: white;
                }
            `}</style>
        </div>
    );
};

export default ChartIntelligence;
