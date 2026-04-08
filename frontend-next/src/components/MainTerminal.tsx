'use client';
import React, { useState, useEffect } from 'react';

const MainTerminal = ({ forceTicker, onAnalysisComplete }: { forceTicker: string | null, onAnalysisComplete?: () => void }) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [ticker, setTicker] = useState('APEX');
    const [progress, setProgress] = useState<string[]>([]);
    const [analysisData, setAnalysisData] = useState<any>(null);
    
    const [error, setError] = useState<string | null>(null);
    const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    useEffect(() => {
        if (forceTicker) {
            setTicker(forceTicker);
            handleAnalyze(forceTicker);
        }
    }, [forceTicker]);
    
    const handleAnalyze = (targetTicker?: string) => {
        const finalTicker = targetTicker || ticker;
        if (!finalTicker) return;
        
        setIsAnalyzing(true);
        setError(null);
        setProgress([]);
        setAnalysisData(null);
        if (!targetTicker) setTicker(finalTicker);

        const eventSource = new EventSource(`${BASE_URL}/api/analyze/stream?ticker=${finalTicker}`);

        eventSource.onmessage = (event) => {
            if (event.data === '[DONE]') {
                eventSource.close();
                setIsAnalyzing(false);
                if (onAnalysisComplete) onAnalysisComplete();
                return;
            }

            try {
                const data = JSON.parse(event.data);
                if (data.type === 'progress') {
                    setProgress(prev => [...prev, data.label]);
                } else if (data.type === 'result') {
                    setAnalysisData(data.payload);
                }
            } catch (err) {
                console.error("Failed to parse SSE event:", err);
                setError("Data processing error. Check backend logs.");
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE Error:", err);
            setError("Connection to analysis engine failed. Is the server running?");
            eventSource.close();
            setIsAnalyzing(false);
        };
    };

    const handleExportPDF = async () => {
        const targetTicker = analysisData?.raw_inputs?.ticker || ticker;
        if (!targetTicker) return;
        
        try {
            const response = await fetch(`${BASE_URL}/api/export/pdf?ticker=${targetTicker}`, {
                headers: {
                    'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || 'dev_default_key'
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Analyst_Report_${targetTicker}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const errorData = await response.json();
                alert(`Export failed: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (err) {
            console.error("PDF Export Error:", err);
            alert("Connection error during PDF export.");
        }
    };

    return (
        <main className="terminal-content">
            {/* TERMINAL TOP INFO BAR */}
            <div className="terminal-header">
                <div className="terminal-title">Apex Terminal Core</div>
                <div style={{ flex: 1, display: 'flex', gap: '32px' }}>
                    <div className="info-stat">
                        <span className="grid-label">Status</span>
                        <div className="grid-value" style={{ color: '#00ff41' }}>CONNECTED.SYSTEM_READY</div>
                    </div>
                    <div className="info-stat">
                        <span className="grid-label">Solvency (Altman-Z)</span>
                        <div className="grid-value" style={{ color: (analysisData?.metrics?.current_z_score > 3.0) ? '#00ff41' : (analysisData?.metrics?.current_z_score > 1.8) ? '#f59e0b' : '#ef4444' }}>
                            {analysisData?.metrics?.current_z_score || '---'} ({analysisData?.metrics?.solvency_signal || 'N/A'})
                        </div>
                    </div>
                    <div className="info-stat">
                        <span className="grid-label">Return on Equity</span>
                        <div className="grid-value" style={{ color: '#0ea5e9' }}>{analysisData?.metrics?.current_roe ? `${analysisData?.metrics?.current_roe}%` : '---'}</div>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <input 
                        className="ticker-input" 
                        placeholder="ENTER TICKER..." 
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    />
                    <button className="analyze-btn" onClick={() => handleAnalyze()} disabled={isAnalyzing}>
                        {isAnalyzing ? 'RUNNING...' : 'EXECUTE ANALYSIS'}
                    </button>
                    {analysisData && (
                        <button className="pdf-btn" onClick={handleExportPDF}>
                            EXPORT PDF
                        </button>
                    )}
                </div>
            </div>

            {/* MAIN DASHBOARD GRID */}
            <div className="dashboard-grid">
                <section className="dashboard-panel panel-left">
                    <div className="panel-header-sub">
                        <span className="grid-label">Analysis Logs</span>
                    </div>
                    <div className="panel-body">
                        {error && (
                            <div className="error-card" style={{ marginBottom: '16px', padding: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', color: '#ef4444', fontSize: '12px' }}>
                                <span style={{ fontWeight: 'bold' }}>[ERROR]</span> {error}
                            </div>
                        )}
                        {isAnalyzing && (
                            <div className="stream-log">
                                {progress.map((step, i) => (
                                    <div key={i} className="stream-line">
                                        <span style={{ color: '#00ff41' }}>[OK]</span> {step}
                                    </div>
                                ))}
                                <div className="stream-line cursor-blink">{">"} FORENSIC_ANALYSIS_IN_PROGRESS...</div>
                            </div>
                        )}
                        {!isAnalyzing && analysisData && (
                            <div className="metrics-view">
                                <h4 className="grid-label" style={{ marginBottom: '16px' }}>Senior Tier Metrics Table (5Y Trends)</h4>
                                <table className="terminal-table">
                                    <thead>
                                        <tr>
                                            <th>FORENSIC METRIC</th>
                                            {analysisData.metrics?.yearly?.map((y: any) => <th key={y.year}>{y.year}</th>)}
                                            <th>SIGNAL</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>REV_CAGR</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.revenue.toLocaleString()}M</td>)}
                                            <td style={{ color: '#00ff41' }}>{analysisData.metrics?.revenue_cagr_pct}%</td>
                                        </tr>
                                        <tr>
                                            <td>DSO (DAYS)</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.dso}</td>)}
                                            <td style={{ color: '#f59e0b' }}>COLLECTION</td>
                                        </tr>
                                        <tr>
                                            <td>INV_TURNOVER</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.inventory_turnover}x</td>)}
                                            <td style={{ color: '#0ea5e9' }}>VELOCITY</td>
                                        </tr>
                                        <tr>
                                            <td>FCF_CONV_PCT</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.fcf_conversion_pct}%</td>)}
                                            <td style={{ color: (analysisData.metrics?.current_fcf_conversion_pct > 80) ? '#00ff41' : '#ef4444' }}>CASH_GEN</td>
                                        </tr>
                                        <tr>
                                            <td>EBITDA_MARG</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.ebitda_margin}%</td>)}
                                            <td style={{ color: '#00ff41' }}>{analysisData.metrics?.margin_signal}</td>
                                        </tr>
                                        <tr>
                                            <td>ASSET_TURNOVER</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.asset_turnover}x</td>)}
                                            <td style={{ color: '#0ea5e9' }}>EFFICIENCY</td>
                                        </tr>
                                        <tr>
                                            <td>RETURN_ON_EQUITY</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.roe}%</td>)}
                                            <td style={{ color: '#00ff41' }}>ROE</td>
                                        </tr>
                                        <tr>
                                            <td>ALTMAN_Z_SCORE</td>
                                            {analysisData.metrics?.yearly?.map((y: any) => <td key={y.year}>{y.z_score}</td>)}
                                            <td style={{ color: (analysisData?.metrics?.current_z_score > 1.8) ? '#00ff41' : '#ef4444' }}>{analysisData.metrics?.solvency_signal}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </section>

                <section className="dashboard-panel panel-right">
                    <div className="panel-header-sub">
                        <span className="grid-label">Analyst Verdict & AI Diagnostics</span>
                    </div>
                    <div className="panel-body diagnosis-container">
                        {!analysisData && !isAnalyzing && (
                            <div className="empty-state-terminal">
                                <p className="terminal-text" style={{ textAlign: 'center' }}>AWAITING COMMAND...</p>
                            </div>
                        )}
                        {(analysisData || isAnalyzing) && (
                            <>
                                <div className="diagnosis-card">
                                    <h4 className="grid-label">Pattern Diagnosis</h4>
                                    <p className="terminal-text">
                                        {analysisData?.analysis?.pattern_diagnosis || 'ANALYZING PATTERNS...'}
                                    </p>
                                </div>
                                <div className="diagnosis-card highlight-card">
                                    <h4 className="grid-label">Analyst Verdict</h4>
                                    <div className="terminal-text" style={{ fontSize: '15px' }}>
                                        <span style={{ color: '#0ea5e9', fontWeight: 'bold' }}>
                                            {analysisData?.analysis?.analyst_verdict_archetype || 'CALCULATING ARCHETYPE...'}
                                        </span>
                                        <p style={{ marginTop: '8px' }}>
                                            {analysisData?.analysis?.analyst_verdict_summary || 'GEN_SUM_IN_PROGRESS...'}
                                        </p>
                                    </div>
                                </div>
                                {analysisData?.analysis?.flags && (
                                    <div className="diagnosis-card" style={{ borderBottom: 'none' }}>
                                        <h4 className="grid-label">Forensic Risk Flags</h4>
                                        <div className="flags-list" style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                            {analysisData.analysis.flags.map((flag: any, i: number) => (
                                                <div key={i} className="flag-item" style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                                    <span style={{ fontSize: '18px' }}>{flag.emoji}</span>
                                                    <div>
                                                        <div style={{ color: '#fff', fontSize: '12px', fontWeight: 'bold' }}>{flag.name}</div>
                                                        <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '2px' }}>{flag.explanation}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </section>
            </div>

            <style jsx>{`
                .dashboard-grid {
                    flex: 1;
                    display: grid;
                    grid-template-rows: 1fr;
                    grid-template-columns: 1.2fr 0.8fr;
                    overflow: hidden;
                    border-top: 1px solid var(--border);
                }
                .dashboard-panel {
                    border-right: 1px solid var(--border);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                .panel-left { background: #000; }
                .panel-right { background: #050505; border-right: none; }
                
                .panel-header-sub {
                    padding: 8px 16px;
                    background: #111;
                    border-bottom: 1px solid var(--border);
                }
                .panel-body {
                    padding: 24px;
                    flex: 1;
                    overflow-y: auto;
                }
                
                .stream-log {
                    font-family: var(--font-mono);
                    font-size: 11px;
                    line-height: 2;
                    color: var(--text-muted);
                }
                .stream-line {
                    display: flex;
                    gap: 8px;
                }
                
                .info-stat {
                    display: flex;
                    flex-direction: column;
                }
                
                .ticker-input {
                    background: #000;
                    border: 1px solid var(--border);
                    color: var(--primary);
                    font-family: var(--font-mono);
                    font-size: 13px;
                    padding: 8px 12px;
                    outline: none;
                    width: 140px;
                }
                .ticker-input:focus { border-color: var(--primary); }
                
                .analyze-btn {
                    background: var(--primary);
                    color: #000;
                    border: none;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 0 20px;
                    cursor: pointer;
                    text-transform: uppercase;
                    transition: all 0.2s;
                }
                .analyze-btn:hover { background: #7dd3fc; }
                .analyze-btn:disabled { background: #334155; color: #94a3b8; cursor: not-allowed; }
                
                .pdf-btn {
                    background: transparent;
                    color: var(--primary);
                    border: 1px solid var(--primary);
                    font-weight: 700;
                    font-size: 11px;
                    padding: 0 16px;
                    cursor: pointer;
                    text-transform: uppercase;
                    transition: all 0.2s;
                }
                .pdf-btn:hover { background: rgba(14, 165, 233, 0.1); }
                
                .diagnosis-container {
                    display: flex;
                    flex-direction: column;
                    gap: 24px;
                }
                .diagnosis-card {
                    padding-bottom: 24px;
                    border-bottom: 1px solid var(--border);
                }
                .highlight-card {
                    padding: 20px;
                    background: rgba(14, 165, 233, 0.05);
                    border: 1px solid var(--primary);
                }
                .terminal-text {
                    margin-top: 12px;
                    line-height: 1.6;
                    color: var(--text-muted);
                    font-size: 13px;
                }
            `}</style>
        </main>
    );
};

export default MainTerminal;
