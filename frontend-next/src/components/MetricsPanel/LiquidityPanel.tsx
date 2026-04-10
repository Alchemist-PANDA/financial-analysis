'use client';

import React from 'react';
import type { FinancialData } from './index';

type LiquidityPanelProps = {
    financialData: FinancialData;
};

const isDisplayableMetric = (value: number | undefined | null) => {
    return value !== undefined && value !== null && Number.isFinite(value) && value !== 0;
};

const formatMetric = (value: number | undefined | null, suffix = '', precision = 1) => {
    if (!isDisplayableMetric(value)) {
        return '';
    }
    return `${Number(value).toFixed(precision)}${suffix}`;
};

const LiquidityPanel = ({ financialData }: LiquidityPanelProps) => {
    const rows = [
        { label: 'Quick Ratio', raw: financialData.current_quick_ratio, value: formatMetric(financialData.current_quick_ratio, '', 2) },
        { label: 'Cash Ratio', raw: financialData.current_cash_ratio, value: formatMetric(financialData.current_cash_ratio, '', 2) },
        {
            label: 'Operating Cash Flow',
            raw: financialData.yearly[financialData.yearly.length - 1]?.ebitda,
            value: formatMetric(financialData.yearly[financialData.yearly.length - 1]?.ebitda, '', 0),
        },
    ];

    return (
        <article className="metrics-card">
                <h3 className="grid-label">Liquidity</h3>
                <table className="terminal-table">
                    <tbody>
                        {rows.filter((row) => isDisplayableMetric(row.raw)).map((row) => (
                            <tr key={row.label}>
                                <td>{row.label}</td>
                                <td>{row.value}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            {isDisplayableMetric(financialData.current_dso) && (
                <p className="signal-line">Current DSO: {financialData.current_dso}</p>
            )}

            <style jsx>{`
                .metrics-card {
                    border: 1px solid var(--border);
                    background: var(--bg-surface);
                    box-shadow: var(--shadow-card);
                    padding: 16px;
                }

                .grid-label {
                    margin-bottom: 12px;
                    display: block;
                }

                .terminal-table td:last-child {
                    color: var(--primary);
                    font-family: var(--font-mono);
                    text-align: right;
                }

                .signal-line {
                    margin-top: 12px;
                    color: var(--text-muted);
                    font-size: 12px;
                }
            `}</style>
        </article>
    );
};

export default LiquidityPanel;
