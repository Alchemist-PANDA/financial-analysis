'use client';

import React, { useMemo, useState } from 'react';
import { FEATURES } from '@/config/features';
import ScorecardComparison from '@/components/ComparisonBoard/Scorecard/ScorecardComparison';
import type { ScorecardResult } from '@/components/MetricsPanel/Scorecard/types';

type CompareAnalysis = {
    ticker: string;
    company_name: string;
    color_signal: 'GREEN' | 'YELLOW' | 'RED';
    metrics: {
        revenue_cagr_pct?: number | null;
        current_z_score?: number | null;
        current_fcf_conversion_pct?: number | null;
        current_roe?: number | null;
        current_dso?: number | null;
    };
    analysis: {
        analyst_verdict_archetype: string;
        analyst_verdict_summary: string;
        retail_verdict?: string;
    };
    scorecard?: ScorecardResult;
};

type ComparePayload = {
    left: CompareAnalysis;
    right: CompareAnalysis;
    verdict: {
        winner: string;
        summary: string;
    };
};

const scoreColor = (signal: 'GREEN' | 'YELLOW' | 'RED') => {
    if (signal === 'GREEN') return '#059669';
    if (signal === 'RED') return '#DC2626';
    return '#D97706';
};

const formatMetric = (value: unknown, precision: number, suffix = '') => {
    const numeric =
        typeof value === 'number'
            ? value
            : typeof value === 'string' && value.trim() !== ''
                ? Number(value)
                : NaN;

    if (!Number.isFinite(numeric)) {
        return '--';
    }

    return `${numeric.toFixed(precision)}${suffix}`;
};

const ComparisonTerminal = () => {
    const [tickerA, setTickerA] = useState('MSFT');
    const [tickerB, setTickerB] = useState('INTC');
    const [isComparing, setIsComparing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<ComparePayload | null>(null);

    const BASE_URL = (typeof window !== 'undefined' ? window.location.origin : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7860')).replace(/\\n/g, '').trim();

    const runComparison = async () => {
        const left = tickerA.trim().toUpperCase();
        const right = tickerB.trim().toUpperCase();
        if (!left || !right) {
            setError('Both ticker fields are required.');
            return;
        }
        if (left === right) {
            setError('Use two different tickers for comparison.');
            return;
        }

        setIsComparing(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch(
                `${BASE_URL}/api/compare?ticker_a=${encodeURIComponent(left)}&ticker_b=${encodeURIComponent(right)}`
            );
            const body = await response.json();
            if (!response.ok) {
                throw new Error(body?.detail || 'Comparison failed.');
            }
            setResult(body as ComparePayload);
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Comparison failed.';
            setError(message);
        } finally {
            setIsComparing(false);
        }
    };

    const keyRows = useMemo(() => {
        if (!result) {
            return [];
        }
        return [
            {
                label: 'Revenue CAGR',
                left: formatMetric(result.left.metrics.revenue_cagr_pct, 1, '%'),
                right: formatMetric(result.right.metrics.revenue_cagr_pct, 1, '%'),
            },
            {
                label: 'Altman Z',
                left: formatMetric(result.left.metrics.current_z_score, 2),
                right: formatMetric(result.right.metrics.current_z_score, 2),
            },
            {
                label: 'FCF Conversion',
                left: formatMetric(result.left.metrics.current_fcf_conversion_pct, 1, '%'),
                right: formatMetric(result.right.metrics.current_fcf_conversion_pct, 1, '%'),
            },
            {
                label: 'ROE',
                left: formatMetric(result.left.metrics.current_roe, 1, '%'),
                right: formatMetric(result.right.metrics.current_roe, 1, '%'),
            },
            {
                label: 'DSO',
                left: formatMetric(result.left.metrics.current_dso, 0, ' days'),
                right: formatMetric(result.right.metrics.current_dso, 0, ' days'),
            },
        ];
    }, [result]);

    return (
        <main className="comparison-container">
            <div className="comparison-header">
                <div className="input-group">
                    <span className="grid-label">Ticker A</span>
                    <input
                        className="ticker-input"
                        value={tickerA}
                        onChange={(e) => {
                            const val = e.target.value.toUpperCase();
                            if (val.length <= 10) setTickerA(val);
                        }}
                    />
                </div>
                <div className="input-group">
                    <span className="grid-label">Ticker B</span>
                    <input
                        className="ticker-input"
                        value={tickerB}
                        onChange={(e) => {
                            const val = e.target.value.toUpperCase();
                            if (val.length <= 10) setTickerB(val);
                        }}
                    />
                </div>
                <button className="analyze-btn compare-btn" onClick={() => void runComparison()} disabled={isComparing}>
                    {isComparing ? 'COMPARING...' : 'RUN COMPARISON'}
                </button>
            </div>

            {error && (
                <div className="error-banner">
                    {error}
                </div>
            )}

            {!result && !isComparing && !error && (
                <div className="empty-state">
                    Enter two tickers and run comparison to generate a side-by-side verdict.
                </div>
            )}

            {isComparing && (
                <div className="empty-state">
                    Running both forensic analyses...
                </div>
            )}

            {result && (
                <div className="comparison-body">
                    <section className="summary-grid">
                        <article className="summary-card">
                            <div className="card-title-row">
                                <h3>{result.left.company_name}</h3>
                                <span style={{ color: scoreColor(result.left.color_signal), fontWeight: 700 }}>
                                    {result.left.ticker}
                                </span>
                            </div>
                            <div className="badge-row">
                                <span className={`verdict-badge badge-${result.left.color_signal.toLowerCase()}`}>
                                    {result.left.analysis.analyst_verdict_archetype}
                                </span>
                            </div>
                            <p className="retail-line">{result.left.analysis.retail_verdict || 'No retail verdict.'}</p>
                            <p className="summary-line">{result.left.analysis.analyst_verdict_summary}</p>
                        </article>

                        <article className="summary-card">
                            <div className="card-title-row">
                                <h3>{result.right.company_name}</h3>
                                <span style={{ color: scoreColor(result.right.color_signal), fontWeight: 700 }}>
                                    {result.right.ticker}
                                </span>
                            </div>
                            <div className="badge-row">
                                <span className={`verdict-badge badge-${result.right.color_signal.toLowerCase()}`}>
                                    {result.right.analysis.analyst_verdict_archetype}
                                </span>
                            </div>
                            <p className="retail-line">{result.right.analysis.retail_verdict || 'No retail verdict.'}</p>
                            <p className="summary-line">{result.right.analysis.analyst_verdict_summary}</p>
                        </article>
                    </section>

                    <section className="table-wrap">
                        <table className="terminal-table">
                            <thead>
                                <tr>
                                    <th>Metric</th>
                                    <th>{result.left.ticker}</th>
                                    <th>{result.right.ticker}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {keyRows.map((row) => (
                                    <tr key={row.label}>
                                        <td>{row.label}</td>
                                        <td>{row.left}</td>
                                        <td>{row.right}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </section>

                    <section className="comparison-verdict-bar">
                        <span className="grid-label" style={{ color: 'var(--primary)' }}>Comparison Verdict</span>
                        <div className="verdict-summary">
                            <strong>{result.verdict.winner}</strong> {result.verdict.summary}
                        </div>
                    </section>
                    {FEATURES.SCORECARD_COMPARE && result.left.scorecard && result.right.scorecard && (
                        <section style={{ marginTop: '16px' }}>
                            <ScorecardComparison left={result.left.scorecard} right={result.right.scorecard} />
                        </section>
                    )}
                </div>
            )}

            <style jsx>{`
                .comparison-container {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    overflow: hidden;
                }

                .comparison-header {
                    display: flex;
                    align-items: flex-end;
                    gap: 12px;
                    padding: 20px 16px;
                    border-bottom: 1px solid var(--border);
                    background: var(--bg-elevated);
                    min-height: 80px;
                    flex-shrink: 0;
                }

                .input-group {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .ticker-input {
                    background: var(--bg-elevated);
                    border: 1px solid var(--border);
                    color: var(--text-primary);
                    font-family: var(--font-mono);
                    font-size: 13px;
                    padding: 8px 12px;
                    width: 140px;
                    outline: none;
                }

                .ticker-input:focus {
                    border-color: var(--primary);
                }

                .analyze-btn {
                    background: linear-gradient(135deg, #2563EB, #1D4ED8);
                    color: #FFFFFF;
                    border: none;
                    font-weight: 700;
                    font-size: 11px;
                    text-transform: uppercase;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .analyze-btn:hover {
                    background: linear-gradient(135deg, #1D4ED8, #1E40AF);
                }

                .analyze-btn:disabled {
                    background: #CBD5E1;
                    color: #64748B;
                    cursor: not-allowed;
                }

                .compare-btn {
                    height: 36px;
                    padding: 0 20px;
                }

                .error-banner {
                    margin: 16px;
                    padding: 12px;
                    border: 1px solid #F87171;
                    background: #FEE2E2;
                    color: #DC2626;
                    font-size: 12px;
                }

                .empty-state {
                    margin: 16px;
                    padding: 24px;
                    border: 1px dashed var(--border);
                    color: var(--text-muted);
                    font-size: 13px;
                    text-align: center;
                }

                .comparison-body {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    padding: 16px;
                    overflow-y: auto;
                }

                .summary-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                }

                .summary-card {
                    border: 1px solid var(--border);
                    background: var(--bg-surface);
                    box-shadow: var(--shadow-card);
                    padding: 16px;
                }

                .card-title-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                }

                .card-title-row h3 {
                    font-size: 16px;
                    margin: 0;
                }

                .badge-row {
                    margin-top: 12px;
                }

                .retail-line {
                    margin-top: 12px;
                    color: var(--foreground);
                    font-size: 13px;
                    font-family: var(--font-mono);
                }

                .summary-line {
                    margin-top: 12px;
                    color: var(--text-muted);
                    font-size: 12px;
                    line-height: 1.6;
                }

                .table-wrap {
                    border: 1px solid var(--border);
                    overflow: hidden;
                }

                .comparison-verdict-bar {
                    padding: 16px;
                    border: 1px solid #DBEAFE;
                    background: #EFF6FF;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .verdict-summary {
                    color: var(--foreground);
                    line-height: 1.6;
                    font-size: 13px;
                }

                @media (max-width: 980px) {
                    .comparison-header {
                        flex-wrap: wrap;
                    }
                    .summary-grid {
                        grid-template-columns: 1fr;
                    }
                }
            `}</style>
        </main>
    );
};

export default ComparisonTerminal;
