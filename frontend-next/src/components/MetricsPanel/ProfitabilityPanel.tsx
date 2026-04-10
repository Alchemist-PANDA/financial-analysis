'use client';

import React from 'react';
import type { FinancialData } from './index';

type ProfitabilityPanelProps = {
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

const ProfitabilityPanel = ({ financialData }: ProfitabilityPanelProps) => {
    const latest = financialData.yearly[financialData.yearly.length - 1];

    const rows = [
        { label: 'ROE', raw: financialData.current_roe, value: formatMetric(financialData.current_roe, '%') },
        { label: 'ROA', raw: financialData.current_roa, value: formatMetric(financialData.current_roa, '%') },
        {
            label: 'ROIC',
            raw: financialData.yearly[financialData.yearly.length - 1]?.net_income / 1,
            value: formatMetric(financialData.yearly[financialData.yearly.length - 1]?.net_income / 1, '%'),
        },
        { label: 'Gross Margin', raw: financialData.current_gross_margin, value: formatMetric(financialData.current_gross_margin, '%') },
        { label: 'EBITDA Margin', raw: latest?.ebitda_margin, value: formatMetric(latest?.ebitda_margin, '%') },
        { label: 'Net Margin', raw: latest?.net_margin, value: formatMetric(latest?.net_margin, '%') },
    ];

    return (
        <article className="metrics-card">
                <h3 className="grid-label">Profitability</h3>
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

export default ProfitabilityPanel;
