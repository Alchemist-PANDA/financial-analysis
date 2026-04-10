'use client';

import React from 'react';
import type { FinancialData } from './index';

type SolvencyPanelProps = {
    financialData: FinancialData;
};

const isDisplayableMetric = (value: number | undefined | null) => {
    return value !== undefined && value !== null && Number.isFinite(value) && value !== 0;
};

const formatMetric = (value: number | undefined | null, suffix = '', precision = 2) => {
    if (!isDisplayableMetric(value)) {
        return '';
    }
    return `${Number(value).toFixed(precision)}${suffix}`;
};

const SolvencyPanel = ({ financialData }: SolvencyPanelProps) => {
    const rows = [
        { label: 'Altman-Z', raw: financialData.current_z_score, value: formatMetric(financialData.current_z_score, '', 2) },
        { label: 'Debt/Equity', raw: financialData.current_debt_equity, value: formatMetric(financialData.current_debt_equity, '', 2) },
        { label: 'Interest Coverage', raw: financialData.current_interest_coverage, value: formatMetric(financialData.current_interest_coverage, '', 2) },
        { label: 'Current Ratio', raw: financialData.current_ratio, value: formatMetric(financialData.current_ratio, '', 2) },
    ];

    return (
        <article className="metrics-card">
                <h3 className="grid-label">Solvency</h3>
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
            {rows.some((row) => isDisplayableMetric(row.raw)) && (
                <p className="signal-line">Signal: {financialData.solvency_signal}</p>
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

export default SolvencyPanel;
