'use client';

import React from 'react';
import type { FinancialData } from './index';

type ValuationPanelProps = {
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

const ValuationPanel = ({ financialData }: ValuationPanelProps) => {
    const rows = [
        { label: 'P/E', raw: financialData.current_pe_ratio, value: formatMetric(financialData.current_pe_ratio, '', 1) },
        { label: 'P/B', raw: financialData.current_pb_ratio, value: formatMetric(financialData.current_pb_ratio, '', 1) },
        { label: 'EV/EBITDA', raw: financialData.current_ev_ebitda, value: formatMetric(financialData.current_ev_ebitda, '', 1) },
    ];

    return (
        <article className="metrics-card">
                <h3 className="grid-label">Valuation</h3>
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
            `}</style>
        </article>
    );
};

export default ValuationPanel;
