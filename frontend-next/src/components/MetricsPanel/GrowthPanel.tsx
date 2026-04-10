'use client';

import React from 'react';
import type { FinancialData } from './index';

type GrowthPanelProps = {
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

const GrowthPanel = ({ financialData }: GrowthPanelProps) => {
    const netIncomeGrowth =
        financialData.yearly[financialData.yearly.length - 2]?.net_income
            ? (financialData.yearly[financialData.yearly.length - 1]?.net_income /
                financialData.yearly[financialData.yearly.length - 2]?.net_income) *
                  100 -
              100
            : null;

    const rows = [
        { label: 'Revenue CAGR', raw: financialData.revenue_cagr_pct, value: formatMetric(financialData.revenue_cagr_pct, '%') },
        { label: 'Net Income Growth', raw: netIncomeGrowth, value: formatMetric(netIncomeGrowth, '%') },
        { label: 'FCF Conversion', raw: financialData.current_fcf_conversion_pct, value: formatMetric(financialData.current_fcf_conversion_pct, '%') },
    ];

    return (
        <article className="metrics-card metrics-card-full">
                <h3 className="grid-label">Growth</h3>
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
                <p className="signal-line">Trajectory: {financialData.revenue_trajectory}</p>
            )}

            <style jsx>{`
                .metrics-card {
                    border: 1px solid var(--border);
                    background: var(--bg-surface);
                    box-shadow: var(--shadow-card);
                    padding: 16px;
                }

                .metrics-card-full {
                    grid-column: 1 / -1;
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

export default GrowthPanel;
