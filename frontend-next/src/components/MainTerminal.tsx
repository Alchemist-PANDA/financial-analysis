'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import ManualEntryModal from './ManualEntryModal';

type ForensicFlag = {
    emoji?: string;
    name: string;
    explanation: string;
};

type YearMetric = {
    year: string;
    revenue: number;
    dso: number;
    inventory_turnover: number;
    fcf_conversion_pct: number;
    ebitda_margin: number;
    asset_turnover: number;
    roe: number;
    z_score: number;
};

type MetricsPayload = {
    yearly: YearMetric[];
    revenue_cagr_pct: number;
    margin_signal: string;
    solvency_signal: string;
    current_z_score: number;
    current_fcf_conversion_pct: number;
};

type AnalysisPayload = {
    pattern_diagnosis: string;
    flags: ForensicFlag[];
    analyst_verdict_archetype: string;
    analyst_verdict_summary: string;
    retail_verdict?: string;
};

type AnalysisResult = {
    ticker: string;
    company_name: string;
    metrics: MetricsPayload;
    analysis: AnalysisPayload;
    color_signal: 'GREEN' | 'YELLOW' | 'RED';
};

type ManualYearInput = {
    year: string;
    revenue: number;
    ebitda: number;
    net_income: number;
    cash: number;
    debt: number;
    total_assets: number;
    equity: number;
    working_capital: number;
    retained_earnings: number;
    ebit: number;
    market_value_equity: number;
    accounts_receivable: number;
    inventory: number;
    capex: number;
};

type ManualAnalysisInput = {
    company: {
        company_name: string;
        sector?: string;
        ticker: string;
    };
    historical_data: ManualYearInput[];
};

type MainTerminalProps = {
    forceTicker?: string | null;
    onAnalysisComplete?: () => void;
};

const formatMetric = (value: number | undefined, suffix = '', precision = 1): string => {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '--';
    }
    return `${value.toFixed(precision)}${suffix}`;
};

const normalizeResultPayload = (raw: unknown, fallbackTicker: string): AnalysisResult | null => {
    if (!raw || typeof raw !== 'object') {
        return null;
    }
    const data = raw as Record<string, unknown>;
    const metrics = data.metrics as MetricsPayload | undefined;
    const analysis = data.analysis as AnalysisPayload | undefined;
    const companyName = typeof data.company_name === 'string' ? data.company_name : fallbackTicker;
    const ticker = typeof data.ticker === 'string' ? data.ticker : fallbackTicker;
    const colorSignal = typeof data.color_signal === 'string' ? data.color_signal : 'YELLOW';

    if (!metrics || !analysis) {
        return null;
    }

    return {
        ticker,
        company_name: companyName,
        metrics,
        analysis,
        color_signal: colorSignal === 'GREEN' || colorSignal === 'RED' ? colorSignal : 'YELLOW',
    };
};

const MainTerminal = ({ forceTicker, onAnalysisComplete }: MainTerminalProps) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [ticker, setTicker] = useState('MSFT');
    const [progress, setProgress] = useState<string[]>([]);
    const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showManualModal, setShowManualModal] = useState(false);

    const eventSourceRef = useRef<EventSource | null>(null);
    const lastForcedTickerRef = useRef<string | null>(null);
    const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\\n/g, '').trim();
    const API_KEY = (process.env.NEXT_PUBLIC_API_KEY || 'dev_default_key').replace(/\\n/g, '').trim();

    const closeEventSource = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
    }, []);

    useEffect(() => {
        return () => {
            closeEventSource();
        };
    }, [closeEventSource]);

    const finalizeAnalysis = useCallback(() => {
        setIsAnalyzing(false);
        onAnalysisComplete?.();
    }, [onAnalysisComplete]);

    const runManualAnalysis = useCallback(async (payload: ManualAnalysisInput) => {
        setProgress([
            'Initializing manual uplink',
            'Normalizing custom figures',
            'Running forensic engine',
        ]);

        try {
            const response = await fetch(`${BASE_URL}/api/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY,
                },
                body: JSON.stringify(payload),
            });

            const body = await response.json();
            if (!response.ok) {
                throw new Error(body?.detail || 'Manual analysis failed.');
            }

            const normalized = normalizeResultPayload(body, payload.company.ticker || 'CUSTOM');
            if (!normalized) {
                throw new Error('Manual analysis returned invalid payload.');
            }

            setAnalysisData(normalized);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Network error during manual analysis.';
            setError(message);
        } finally {
            finalizeAnalysis();
        }
    }, [API_KEY, BASE_URL, finalizeAnalysis]);

    const handleAnalyze = useCallback(async (targetTicker?: string, manualPayload?: ManualAnalysisInput) => {
        const resolvedTicker = (targetTicker || ticker).trim().toUpperCase();
        if (!resolvedTicker && !manualPayload) {
            return;
        }

        closeEventSource();
        setIsAnalyzing(true);
        setError(null);
        setProgress([]);
        setAnalysisData(null);

        if (manualPayload) {
            await runManualAnalysis(manualPayload);
            return;
        }

        setTicker(resolvedTicker);
        const streamUrl = `${BASE_URL}/api/analyze/stream?ticker=${encodeURIComponent(resolvedTicker)}`;
        const eventSource = new EventSource(streamUrl);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
            if (event.data === '[DONE]') {
                closeEventSource();
                finalizeAnalysis();
                return;
            }

            try {
                const payload = JSON.parse(event.data) as {
                    type?: string;
                    label?: string;
                    payload?: unknown;
                    message?: string;
                };

                if (payload.type === 'progress' && payload.label) {
                    const label = payload.label;
                    setProgress((prev) => [...prev, label].slice(-8));
                    return;
                }

                if (payload.type === 'error') {
                    setError(payload.message || 'Analysis failed.');
                    return;
                }

                if (payload.type === 'result') {
                    const normalized = normalizeResultPayload(payload.payload, resolvedTicker);
                    if (normalized) {
                        setAnalysisData(normalized);
                    } else {
                        setError('Unexpected analysis response.');
                    }
                }
            } catch {
                setError('Failed to parse streaming response.');
            }
        };

        eventSource.onerror = () => {
            closeEventSource();
            setError('Analysis stream disconnected. Please retry.');
            finalizeAnalysis();
        };
    }, [ticker, closeEventSource, runManualAnalysis, BASE_URL, finalizeAnalysis]);

    useEffect(() => {
        if (!forceTicker) {
            return;
        }

        const normalized = forceTicker.trim().toUpperCase();
        if (!normalized || lastForcedTickerRef.current === normalized) {
            return;
        }

        lastForcedTickerRef.current = normalized;
        setTicker(normalized);
        void handleAnalyze(normalized);
    }, [forceTicker, handleAnalyze]);

    const handleExportPDF = useCallback(async () => {
        if (!analysisData?.ticker) {
            return;
        }

        try {
            const response = await fetch(
                `${BASE_URL}/api/export/pdf?ticker=${encodeURIComponent(analysisData.ticker)}`,
                {
                    headers: {
                        'X-API-Key': API_KEY,
                    },
                }
            );

            if (!response.ok) {
                const errorPayload = await response.json();
                throw new Error(errorPayload?.detail || 'Failed to export PDF report.');
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const anchor = document.createElement('a');
            anchor.href = downloadUrl;
            anchor.download = `Analyst_Report_${analysisData.ticker}.pdf`;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'PDF export failed.';
            setError(message);
        }
    }, [API_KEY, analysisData?.ticker, BASE_URL]);

    return (
        <main className="terminal-content">
            <ManualEntryModal
                isOpen={showManualModal}
                onClose={() => setShowManualModal(false)}
                onSubmit={(payload) => {
                    void handleAnalyze(undefined, payload);
                }}
            />

            <div className="terminal-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div className="terminal-title">Sentinel Forensic</div>
                    {analysisData?.color_signal && (
                        <div className={`verdict-badge badge-${analysisData.color_signal.toLowerCase()}`}>
                            {analysisData.analysis.analyst_verdict_archetype}
                        </div>
                    )}
                </div>

                <div style={{ flex: 1, display: 'flex', gap: '24px' }}>
                    <div className="info-stat">
                        <span className="grid-label">Retail Verdict</span>
                        <div
                            className="grid-value"
                            style={{
                                color:
                                    analysisData?.color_signal === 'GREEN'
                                        ? '#00ff41'
                                        : analysisData?.color_signal === 'RED'
                                            ? '#ef4444'
                                            : '#f59e0b',
                                fontSize: '11px',
                                maxWidth: '240px',
                                lineHeight: '1.2',
                            }}
                        >
                            {analysisData?.analysis.retail_verdict ||
                                (isAnalyzing ? 'ANALYZING...' : 'AWAITING COMMAND')}
                        </div>
                    </div>
                    <div className="info-stat">
                        <span className="grid-label">Solvency (Altman-Z)</span>
                        <div
                            className="grid-value"
                            style={{
                                color:
                                    (analysisData?.metrics.current_z_score || 0) > 3.0
                                        ? '#00ff41'
                                        : (analysisData?.metrics.current_z_score || 0) > 1.8
                                            ? '#f59e0b'
                                            : '#ef4444',
                            }}
                        >
                            {analysisData?.metrics.current_z_score ?? '---'}
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="manual-btn" onClick={() => setShowManualModal(true)}>
                        MANUAL ENTRY
                    </button>
                    <input
                        className="ticker-input"
                        placeholder="ENTER TICKER..."
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !isAnalyzing) {
                                void handleAnalyze();
                            }
                        }}
                    />
                    <button className="analyze-btn" onClick={() => void handleAnalyze()} disabled={isAnalyzing}>
                        {isAnalyzing ? 'RUNNING...' : 'EXECUTE'}
                    </button>
                    {analysisData && (
                        <button className="pdf-btn" onClick={() => void handleExportPDF()}>
                            PDF
                        </button>
                    )}
                </div>
            </div>

            <div className="dashboard-grid">
                <section className="dashboard-panel panel-left">
                    <div className="panel-header-sub">
                        <span className="grid-label">Analysis Logs</span>
                    </div>
                    <div className="panel-body">
                        {error && (
                            <div
                                className="error-card"
                                style={{
                                    marginBottom: '16px',
                                    padding: '12px',
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    border: '1px solid #ef4444',
                                    color: '#ef4444',
                                    fontSize: '12px',
                                }}
                            >
                                <span style={{ fontWeight: 'bold' }}>[ERROR]</span> {error}
                            </div>
                        )}
                        {isAnalyzing && (
                            <div className="stream-log">
                                {progress.map((step, index) => (
                                    <div key={`${step}-${index}`} className="stream-line">
                                        <span style={{ color: '#00ff41' }}>[OK]</span> {step}
                                    </div>
                                ))}
                                <div className="stream-line cursor-blink">{'>'} FORENSIC_ANALYSIS_IN_PROGRESS...</div>
                            </div>
                        )}
                        {!isAnalyzing && analysisData && (
                            <div className="metrics-view">
                                <h4 className="grid-label" style={{ marginBottom: '16px' }}>
                                    Senior Tier Metrics Table (5Y Trends)
                                </h4>
                                <table className="terminal-table">
                                    <thead>
                                        <tr>
                                            <th>FORENSIC METRIC</th>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <th key={year.year}>{year.year}</th>
                                            ))}
                                            <th>SIGNAL</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>REV_CAGR</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{year.revenue.toLocaleString()}M</td>
                                            ))}
                                            <td style={{ color: '#00ff41' }}>
                                                {formatMetric(analysisData.metrics.revenue_cagr_pct, '%')}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>DSO (DAYS)</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{year.dso}</td>
                                            ))}
                                            <td style={{ color: '#f59e0b' }}>COLLECTION</td>
                                        </tr>
                                        <tr>
                                            <td>INV_TURNOVER</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.inventory_turnover, 'x')}</td>
                                            ))}
                                            <td style={{ color: '#0ea5e9' }}>VELOCITY</td>
                                        </tr>
                                        <tr>
                                            <td>FCF_CONV_PCT</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.fcf_conversion_pct, '%')}</td>
                                            ))}
                                            <td
                                                style={{
                                                    color:
                                                        analysisData.metrics.current_fcf_conversion_pct > 80
                                                            ? '#00ff41'
                                                            : '#ef4444',
                                                }}
                                            >
                                                CASH_GEN
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>EBITDA_MARG</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.ebitda_margin, '%')}</td>
                                            ))}
                                            <td style={{ color: '#00ff41' }}>{analysisData.metrics.margin_signal}</td>
                                        </tr>
                                        <tr>
                                            <td>ASSET_TURNOVER</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.asset_turnover, 'x', 2)}</td>
                                            ))}
                                            <td style={{ color: '#0ea5e9' }}>EFFICIENCY</td>
                                        </tr>
                                        <tr>
                                            <td>RETURN_ON_EQUITY</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.roe, '%')}</td>
                                            ))}
                                            <td style={{ color: '#00ff41' }}>ROE</td>
                                        </tr>
                                        <tr>
                                            <td>ALTMAN_Z_SCORE</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.z_score, '', 2)}</td>
                                            ))}
                                            <td
                                                style={{
                                                    color:
                                                        analysisData.metrics.current_z_score > 1.8
                                                            ? '#00ff41'
                                                            : '#ef4444',
                                                }}
                                            >
                                                {analysisData.metrics.solvency_signal}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        )}
                        {!isAnalyzing && !analysisData && (
                            <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                                No output yet. Execute a ticker or run manual entry.
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
                                <p className="terminal-text" style={{ textAlign: 'center' }}>
                                    AWAITING COMMAND...
                                </p>
                            </div>
                        )}
                        {(analysisData || isAnalyzing) && (
                            <>
                                <div className="diagnosis-card">
                                    <h4 className="grid-label">Pattern Diagnosis</h4>
                                    <p className="terminal-text">
                                        {analysisData?.analysis.pattern_diagnosis || 'ANALYZING PATTERNS...'}
                                    </p>
                                </div>
                                <div className="diagnosis-card highlight-card">
                                    <h4 className="grid-label">Analyst Verdict</h4>
                                    <div className="terminal-text" style={{ fontSize: '15px' }}>
                                        <span style={{ color: '#0ea5e9', fontWeight: 'bold' }}>
                                            {analysisData?.analysis.analyst_verdict_archetype || 'CALCULATING ARCHETYPE...'}
                                        </span>
                                        <p style={{ marginTop: '8px' }}>
                                            {analysisData?.analysis.analyst_verdict_summary || 'GEN_SUM_IN_PROGRESS...'}
                                        </p>
                                    </div>
                                </div>
                                {!!analysisData?.analysis.flags?.length && (
                                    <div className="diagnosis-card" style={{ borderBottom: 'none' }}>
                                        <h4 className="grid-label">Forensic Risk Flags</h4>
                                        <div
                                            className="flags-list"
                                            style={{
                                                marginTop: '12px',
                                                display: 'flex',
                                                flexDirection: 'column',
                                                gap: '12px',
                                            }}
                                        >
                                            {analysisData.analysis.flags.map((flag, index) => (
                                                <div
                                                    key={`${flag.name}-${index}`}
                                                    className="flag-item"
                                                    style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}
                                                >
                                                    <span style={{ fontSize: '18px' }}>{flag.emoji || '!'}</span>
                                                    <div>
                                                        <div
                                                            style={{
                                                                color: '#fff',
                                                                fontSize: '12px',
                                                                fontWeight: 'bold',
                                                            }}
                                                        >
                                                            {flag.name}
                                                        </div>
                                                        <div
                                                            style={{
                                                                color: 'var(--text-muted)',
                                                                fontSize: '11px',
                                                                marginTop: '2px',
                                                            }}
                                                        >
                                                            {flag.explanation}
                                                        </div>
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

                .panel-left {
                    background: #000;
                }

                .panel-right {
                    background: #050505;
                    border-right: none;
                }

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

                .ticker-input:focus {
                    border-color: var(--primary);
                }

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

                .analyze-btn:hover {
                    background: #7dd3fc;
                }

                .analyze-btn:disabled {
                    background: #334155;
                    color: #94a3b8;
                    cursor: not-allowed;
                }

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

                .pdf-btn:hover {
                    background: rgba(14, 165, 233, 0.1);
                }

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

                @media (max-width: 1200px) {
                    .terminal-header {
                        height: auto;
                        min-height: 48px;
                        flex-wrap: wrap;
                        padding: 12px 16px;
                    }
                    .dashboard-grid {
                        grid-template-columns: 1fr;
                        grid-template-rows: 1fr 1fr;
                    }
                    .dashboard-panel {
                        border-right: none;
                        border-bottom: 1px solid var(--border);
                    }
                    .panel-right {
                        border-bottom: none;
                    }
                }

                @media (max-width: 720px) {
                    .ticker-input {
                        width: 110px;
                    }
                    .panel-body {
                        padding: 16px;
                    }
                }
            `}</style>
        </main>
    );
};

export default MainTerminal;
