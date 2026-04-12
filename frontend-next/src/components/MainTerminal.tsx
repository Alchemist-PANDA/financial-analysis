'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { safeFetch } from '@/utils/api';
import ManualEntryModal from './ManualEntryModal';
import { FEATURES } from '@/config/features';
import ScorecardPanel from '@/components/MetricsPanel/Scorecard/ScorecardPanel';
import AnalysisHistory, { type ScorecardHistoryItem } from '@/components/MetricsPanel/Scorecard/AnalysisHistory';
import type { ScorecardResult } from '@/components/MetricsPanel/Scorecard/types';

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

export type MetricsPayload = {
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
    scorecard?: ScorecardResult;
    scorecard_error?: string;
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
    onDataLoaded?: (data: MetricsPayload) => void;
    onTickerChange?: (ticker: string) => void;
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
    
    // Defensive extraction with fallbacks
    const rawMetrics = data.metrics as Record<string, any> | undefined;
    const metrics: MetricsPayload = {
        yearly: Array.isArray(rawMetrics?.yearly) ? rawMetrics!.yearly : [],
        revenue_cagr_pct: typeof rawMetrics?.revenue_cagr_pct === 'number' ? rawMetrics!.revenue_cagr_pct : 0,
        margin_signal: typeof rawMetrics?.margin_signal === 'string' ? rawMetrics!.margin_signal : 'STABLE',
        solvency_signal: typeof rawMetrics?.solvency_signal === 'string' ? rawMetrics!.solvency_signal : 'SAFE',
        current_z_score: typeof rawMetrics?.current_z_score === 'number' ? rawMetrics!.current_z_score : 0,
        current_fcf_conversion_pct: typeof rawMetrics?.current_fcf_conversion_pct === 'number' ? rawMetrics!.current_fcf_conversion_pct : 0,
    };

    const rawAnalysis = data.analysis as Record<string, any> | undefined;
    const analysis: AnalysisPayload = {
        pattern_diagnosis: typeof rawAnalysis?.pattern_diagnosis === 'string' ? rawAnalysis!.pattern_diagnosis : 'No diagnosis available.',
        flags: Array.isArray(rawAnalysis?.flags) ? rawAnalysis!.flags : [],
        analyst_verdict_archetype: typeof rawAnalysis?.analyst_verdict_archetype === 'string' ? rawAnalysis!.analyst_verdict_archetype : 'NEUTRAL',
        analyst_verdict_summary: typeof rawAnalysis?.analyst_verdict_summary === 'string' ? rawAnalysis!.analyst_verdict_summary : 'No summary available.',
        retail_verdict: typeof rawAnalysis?.retail_verdict === 'string' ? rawAnalysis!.retail_verdict : undefined,
    };

    const companyName = typeof data.company_name === 'string' ? data.company_name : fallbackTicker;
    const ticker = typeof data.ticker === 'string' ? data.ticker : fallbackTicker;
    const colorSignal = typeof data.color_signal === 'string' ? data.color_signal : 'YELLOW';
    const scorecard = (data.scorecard as ScorecardResult | undefined) ?? undefined;
    const scorecardError = typeof data.scorecard_error === 'string' ? data.scorecard_error : undefined;

    return {
        ticker,
        company_name: companyName,
        metrics,
        analysis,
        color_signal: colorSignal === 'GREEN' || colorSignal === 'RED' ? colorSignal : 'YELLOW',
        scorecard,
        scorecard_error: scorecardError,
    };
};

const MainTerminal = ({ forceTicker, onAnalysisComplete, onDataLoaded }: MainTerminalProps) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [ticker, setTicker] = useState('MSFT');
    const [progress, setProgress] = useState<string[]>([]);
    const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showManualModal, setShowManualModal] = useState(false);
    const [scorecardResult, setScorecardResult] = useState<ScorecardResult | null>(null);
    const [scorecardView, setScorecardView] = useState<'simple' | 'expert'>('simple');
    const [scorecardMode, setScorecardMode] = useState<'credit' | 'investment'>('credit');
    const [scorecardHistory, setScorecardHistory] = useState<ScorecardHistoryItem[]>([]);
    const [scorecardHistoryError, setScorecardHistoryError] = useState<string | null>(null);

    const eventSourceRef = useRef<EventSource | null>(null);
    const lastForcedTickerRef = useRef<string | null>(null);
    
    // Direct link to backend to bypass Vercel proxy issues
    const BACKEND_PROD_URL = "https://ghouri112-financial-terminal-backend.hf.space";
    const BASE_URL = (typeof window !== 'undefined' && (window.location.hostname.includes('vercel.app') || window.location.hostname.includes('github.dev'))) 
        ? BACKEND_PROD_URL 
        : (typeof window !== 'undefined' ? window.location.origin : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7860')).replace(/\\n/g, '').trim();
    
    const API_KEY = (process.env.NEXT_PUBLIC_API_KEY || 'dev_default_key').replace(/\\n/g, '').trim();

    const closeEventSource = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.onmessage = null;
            eventSourceRef.current.onerror = null;
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
    }, []);

    useEffect(() => {
        return () => {
            closeEventSource();
        };
    }, [closeEventSource]);

    useEffect(() => {
        if (!FEATURES.SCORECARD_HISTORY) {
            return;
        }
        let isActive = true;
        const loadHistory = async () => {
            setScorecardHistoryError(null);
            try {
                const response = await safeFetch(`${BASE_URL}/api/scorecard/history`, {
                    headers: { 'X-API-Key': API_KEY },
                });
                
                if (!response.success) {
                    throw new Error(response.error);
                }

                if (isActive) {
                    setScorecardHistory(Array.isArray(response.data) ? response.data : []);
                }
            } catch (err) {
                if (isActive) {
                    const message = err instanceof Error ? err.message : 'Failed to load scorecard history.';
                    setScorecardHistoryError(message);
                    setScorecardHistory([]);
                }
            }
        };
        void loadHistory();
        return () => {
            isActive = false;
        };
    }, [API_KEY, BASE_URL]);

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
            const response = await safeFetch(`${BASE_URL}/api/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY,
                },
                body: JSON.stringify(payload),
            });

            if (!response.success) {
                throw new Error(response.error);
            }

            const normalized = normalizeResultPayload(response.data, payload.company.ticker || 'CUSTOM');
            if (!normalized) {
                throw new Error('Manual analysis returned invalid payload.');
            }

            setAnalysisData(normalized);
            setScorecardResult(normalized.scorecard ?? null);
            if (normalized.scorecard?.scoring_mode) {
                setScorecardMode(normalized.scorecard.scoring_mode);
            }
            onDataLoaded?.(normalized.metrics);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Network error during manual analysis.';
            setError(message);
        } finally {
            finalizeAnalysis();
        }
    }, [API_KEY, BASE_URL, finalizeAnalysis, onDataLoaded]);

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
        setScorecardResult(null);

        if (manualPayload) {
            await runManualAnalysis(manualPayload);
            return;
        }

        setTicker(resolvedTicker);
        onTickerChange?.(resolvedTicker);
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
                        setScorecardResult(normalized.scorecard ?? null);
                        if (normalized.scorecard?.scoring_mode) {
                            setScorecardMode(normalized.scorecard.scoring_mode);
                        }
                        onDataLoaded?.(normalized.metrics);
                    } else {
                        setError('Unexpected analysis response.');
                    }
                }
            } catch {
                setError('Failed to parse streaming response.');
            }
        };

        eventSource.onerror = (err) => {
            console.error('SSE Error:', err);
            closeEventSource();
            setError('Backend analysis failed or timed out. Please ensure the backend is running and try again.');
            finalizeAnalysis();
        };
    }, [ticker, closeEventSource, runManualAnalysis, BASE_URL, finalizeAnalysis, onDataLoaded]);

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

    const handleScorecardModeChange = useCallback(async (mode: 'credit' | 'investment') => {
        if (!scorecardResult?.inputs) {
            setScorecardMode(mode);
            return;
        }
        setScorecardMode(mode);
        try {
            const response = await fetch(`${BASE_URL}/api/scorecard/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY,
                },
                body: JSON.stringify({
                    ...scorecardResult.inputs,
                    scoring_mode: mode,
                }),
            });
            const body = await response.json();
            if (!response.ok) {
                throw new Error(body?.detail || 'Scorecard re-run failed.');
            }
            setScorecardResult(body as ScorecardResult);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Scorecard re-run failed.';
            setError(message);
        }
    }, [API_KEY, BASE_URL, scorecardResult]);

    const handleScorecardSelect = useCallback((item: ScorecardHistoryItem) => {
        setScorecardResult(item.result);
        setScorecardMode(item.result.scoring_mode || 'credit');
        setScorecardView('simple');
    }, []);

    const handleScorecardRecalculate = useCallback(async (item: ScorecardHistoryItem) => {
        try {
            const response = await fetch(`${BASE_URL}/api/scorecard/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY,
                },
                body: JSON.stringify({
                    ...item.inputs,
                    scoring_mode: item.result.scoring_mode,
                }),
            });
            const body = await response.json();
            if (!response.ok) {
                throw new Error(body?.detail || 'Scorecard recalculation failed.');
            }
            setScorecardResult(body as ScorecardResult);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Scorecard recalculation failed.';
            setError(message);
        }
    }, [API_KEY, BASE_URL]);

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
                                        ? '#059669'
                                        : analysisData?.color_signal === 'RED'
                                            ? '#DC2626'
                                            : '#D97706',
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
                                        ? '#059669'
                                        : (analysisData?.metrics.current_z_score || 0) > 1.8
                                            ? '#D97706'
                                            : '#DC2626',
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
                        onChange={(e) => {
                            const val = e.target.value.toUpperCase();
                            if (val.length <= 10) setTicker(val);
                        }}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !isAnalyzing) {
                                void handleAnalyze();
                            }
                        }}
                    />
                    <button className="analyze-btn" onClick={() => void handleAnalyze()} disabled={isAnalyzing}>
                        {isAnalyzing ? 'RUNNING...' : 'RUN AI FORENSIC'}
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
                                    background: '#FEE2E2',
                                    border: '1px solid #F87171',
                                    color: '#DC2626',
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
                                        <span style={{ color: '#059669' }}>[OK]</span> {step}
                                    </div>
                                ))}
                                <div className="stream-line cursor-blink">{'>'} FORENSIC_ANALYSIS_IN_PROGRESS...</div>
                            </div>
                        )}
                        {!isAnalyzing && analysisData && (
                            <div className="metrics-view">
                                {FEATURES.SCORECARD_PANEL && scorecardResult && (
                                    <div className="stream-log" style={{ marginBottom: '16px' }}>
                                        <div className="stream-line">-&gt; [1/5] Validating inputs...</div>
                                        <div className="stream-line">-&gt; [2/5] Running metrics engine...</div>
                                        <div className="stream-line">
                                            -&gt; [3/5] Scoring: Health {scorecardResult.health_score}/100 - {scorecardResult.health_band}
                                        </div>
                                        <div className="stream-line">-&gt; [4/5] Generating narrative...</div>
                                        <div className="stream-line">
                                            -&gt; [5/5] Persisting to database (model v{scorecardResult.scoring_model_version})...
                                        </div>
                                        <div className="stream-line">-&gt; COMPLETE. Analysis ID: {scorecardResult.analysis_id ?? 'N/A'}</div>
                                    </div>
                                )}
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
                                            <td style={{ color: '#059669' }}>
                                                {formatMetric(analysisData.metrics.revenue_cagr_pct, '%')}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>DSO (DAYS)</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{year.dso}</td>
                                            ))}
                                            <td style={{ color: '#D97706' }}>COLLECTION</td>
                                        </tr>
                                        <tr>
                                            <td>INV_TURNOVER</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.inventory_turnover, 'x')}</td>
                                            ))}
                                            <td style={{ color: '#0891B2' }}>VELOCITY</td>
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
                                                            ? '#059669'
                                                            : '#DC2626',
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
                                            <td style={{ color: '#059669' }}>{analysisData.metrics.margin_signal}</td>
                                        </tr>
                                        <tr>
                                            <td>ASSET_TURNOVER</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.asset_turnover, 'x', 2)}</td>
                                            ))}
                                            <td style={{ color: '#0891B2' }}>EFFICIENCY</td>
                                        </tr>
                                        <tr>
                                            <td>RETURN_ON_EQUITY</td>
                                            {analysisData.metrics.yearly.map((year) => (
                                                <td key={year.year}>{formatMetric(year.roe, '%')}</td>
                                            ))}
                                            <td style={{ color: '#059669' }}>ROE</td>
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
                                                            ? '#059669'
                                                            : '#DC2626',
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
                            <div className="empty-command-center">
                                <div className="command-box">
                                    <div className="command-icon">⚛️</div>
                                    <h2 className="command-title">Institutional AI Terminal</h2>
                                    <p className="command-subtitle">Enter a ticker to begin multi-signal forensic analysis.</p>
                                    <div className="command-input-wrapper">
                                        <input
                                            className="command-input"
                                            placeholder="ENTER TICKER (e.g. TM, AAPL, NVDA)..."
                                            value={ticker}
                                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                                            onKeyDown={(e) => e.key === 'Enter' && void handleAnalyze()}
                                        />
                                        <button className="command-btn" onClick={() => void handleAnalyze()}>
                                            RUN FORENSIC AI
                                        </button>
                                    </div>
                                    <div className="command-hints">
                                        <span>TIP: Try "TM" for international ADR analysis</span>
                                        <span>•</span>
                                        <span>Manual entry supported</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </section>

                <section className="dashboard-panel panel-right">
                    <div className="panel-header-sub">
                        <span className="grid-label">Analyst Verdict & AI Diagnostics</span>
                    </div>
                    <div className="panel-body diagnosis-container">
                        {!analysisData && !isAnalyzing && !scorecardResult && (
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
                                        <span style={{ color: '#2563EB', fontWeight: 'bold' }}>
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
                                                                color: '#0F172A',
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

                        {FEATURES.SCORECARD_PANEL && (
                            scorecardResult ? (
                                <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid var(--border-subtle)' }}>
                                    <h4 className="grid-label" style={{ marginBottom: '16px' }}>Forensic Scorecard</h4>
                                    <ScorecardPanel
                                        result={scorecardResult}
                                        view={scorecardView}
                                        mode={scorecardMode}
                                        onModeChange={handleScorecardModeChange}
                                        onViewChange={setScorecardView}
                                    />
                                    {FEATURES.SCORECARD_HISTORY && (
                                        <div style={{ marginTop: '20px' }}>
                                            {scorecardHistoryError && (
                                                <div style={{ color: '#DC2626', fontSize: '11px', marginBottom: '8px' }}>
                                                    {scorecardHistoryError}
                                                </div>
                                            )}
                                            <AnalysisHistory
                                                items={scorecardHistory}
                                                onSelect={handleScorecardSelect}
                                                onRecalculate={handleScorecardRecalculate}
                                            />
                                        </div>
                                    )}
                                </div>
                            ) : (
                                (isAnalyzing) && (
                                    <div className="empty-state-terminal" style={{ marginTop: '20px', borderTop: '1px solid var(--border-subtle)', paddingTop: '20px' }}>
                                        <p className="terminal-text" style={{ textAlign: 'center' }}>
                                            AWAITING SCORECARD...
                                        </p>
                                        {analysisData?.scorecard_error && (
                                            <p style={{ marginTop: '8px', color: '#DC2626', fontSize: '11px', textAlign: 'center' }}>
                                                SCORECARD ERROR: {analysisData.scorecard_error}
                                            </p>
                                        )}
                                    </div>
                                )
                            )
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
                    background: var(--bg-surface);
                }

                .panel-right {
                    background: var(--bg-surface);
                    border-right: none;
                }

                .panel-header-sub {
                    padding: 8px 16px;
                    background: var(--bg-elevated);
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
                    background: var(--bg-elevated);
                    border: 1px solid var(--border);
                    color: var(--text-primary);
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
                    background: linear-gradient(135deg,#2563EB,#1D4ED8);
                    color: #FFFFFF;
                    border: none;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 0 20px;
                    cursor: pointer;
                    text-transform: uppercase;
                    transition: all 0.2s;
                }

                .analyze-btn:hover {
                    background: linear-gradient(135deg,#1D4ED8,#1E40AF);
                }

                .analyze-btn:disabled {
                    background: #CBD5E1;
                    color: #64748B;
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
                    background: rgba(37, 99, 235, 0.1);
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

                .empty-command-center {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    min-height: 400px;
                }

                .command-box {
                    text-align: center;
                    background: var(--bg-surface);
                    border: 1px solid var(--border);
                    padding: 48px;
                    max-width: 600px;
                    width: 100%;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.1);
                }

                .command-icon {
                    font-size: 48px;
                    margin-bottom: 16px;
                }

                .command-title {
                    font-size: 24px;
                    font-weight: 800;
                    color: var(--primary);
                    margin-bottom: 8px;
                    letter-spacing: -0.02em;
                }

                .command-subtitle {
                    color: var(--text-muted);
                    font-size: 14px;
                    margin-bottom: 32px;
                }

                .command-input-wrapper {
                    display: flex;
                    gap: 0;
                    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.1);
                }

                .command-input {
                    flex: 1;
                    background: var(--bg-elevated);
                    border: 1px solid var(--primary);
                    color: var(--text-primary);
                    padding: 16px 20px;
                    font-family: var(--font-mono);
                    font-size: 15px;
                    outline: none;
                }

                .command-btn {
                    background: linear-gradient(135deg,#2563EB,#1D4ED8);
                    color: white;
                    border: none;
                    padding: 0 24px;
                    font-weight: 800;
                    font-size: 12px;
                    text-transform: uppercase;
                    cursor: pointer;
                }

                .command-hints {
                    margin-top: 24px;
                    display: flex;
                    justify-content: center;
                    gap: 12px;
                    font-size: 11px;
                    color: var(--text-muted);
                }

                .highlight-card {
                    padding: 20px;
                    background: #EFF6FF;
                    border: 1px solid #DBEAFE;
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
