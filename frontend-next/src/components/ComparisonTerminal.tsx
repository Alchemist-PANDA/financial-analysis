'use client';

import React, { useMemo, useState } from 'react';

type CompareAnalysis = {
    ticker: string;
    company_name: string;
    color_signal: 'GREEN' | 'YELLOW' | 'RED';
    metrics: {
        revenue_cagr_pct: number;
        current_z_score: number;
        current_fcf_conversion_pct: number;
        current_roe: number;
        current_dso: number;
    };
    analysis: {
        analyst_verdict_archetype: string;
        analyst_verdict_summary: string;
        retail_verdict?: string;
    };
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
    if (signal === 'GREEN') return '#00ff41';
    if (signal === 'RED') return '#ef4444';
    return '#f59e0b';
};

const ComparisonTerminal = () => {
    const [tickerA, setTickerA] = useState('MSFT');
    const [tickerB, setTickerB] = useState('INTC');
    const [isComparing, setIsComparing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<ComparePayload | null>(null);

    const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\\n/g, '').trim();

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
                left: `${result.left.metrics.revenue_cagr_pct.toFixed(1)}%`,
                right: `${result.right.metrics.revenue_cagr_pct.toFixed(1)}%`,
            },
            {
                label: 'Altman Z',
                left: result.left.metrics.current_z_score.toFixed(2),
                right: result.right.metrics.current_z_score.toFixed(2),
            },
            {
                label: 'FCF Conversion',
                left: `${result.left.metrics.current_fcf_conversion_pct.toFixed(1)}%`,
                right: `${result.right.metrics.current_fcf_conversion_pct.toFixed(1)}%`,
            },
            {
                label: 'ROE',
                left: `${result.left.metrics.current_roe.toFixed(1)}%`,
                right: `${result.right.metrics.current_roe.toFixed(1)}%`,
            },
            {
                label: 'DSO',
                left: `${result.left.metrics.current_dso.toFixed(0)} days`,
                right: `${result.right.metrics.current_dso.toFixed(0)} days`,
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
                        onChange={(e) => setTickerA(e.target.value.toUpperCase())}
                    />
                </div>
                <div className="input-group">
                    <span className="grid-label">Ticker B</span>
                    <input
                        className="ticker-input"
                        value={tickerB}
                        onChange={(e) => setTickerB(e.target.value.toUpperCase())}
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
                    align-items: end;
                    gap: 12px;
                    padding: 16px;
                    border-bottom: 1px solid var(--border);
                    background: #050505;
                }

                .input-group {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .ticker-input {
                    background: #000;
                    border: 1px solid var(--border);
                    color: var(--primary);
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
                    background: var(--primary);
                    color: #000;
                    border: none;
                    font-weight: 700;
                    font-size: 11px;
                    text-transform: uppercase;
                    cursor: pointer;
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

                .compare-btn {
                    height: 36px;
                    padding: 0 20px;
                }

                .error-banner {
                    margin: 16px;
                    padding: 12px;
                    border: 1px solid #ef4444;
                    background: rgba(239, 68, 68, 0.12);
                    color: #ef4444;
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
                    background: #040404;
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
                    border: 1px solid var(--primary);
                    background: rgba(14, 165, 233, 0.08);
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
