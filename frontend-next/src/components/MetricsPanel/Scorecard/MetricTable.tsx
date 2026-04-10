import React from 'react';

type MetricTableProps = {
    metrics: Record<string, number | Record<string, number> | undefined>;
    statuses: Record<string, string>;
    benchmarks: Record<string, string>;
    altmanZone?: string;
};

const METRIC_ROWS = [
    { key: 'roic', label: 'ROIC', format: 'pct' },
    { key: 'incremental_roic', label: 'Incremental ROIC', format: 'pct' },
    { key: 'ebit_margin', label: 'EBIT Margin', format: 'pct' },
    { key: 'net_debt_to_ebitda', label: 'Net Debt/EBITDA', format: 'x' },
    { key: 'interest_coverage', label: 'Interest Coverage', format: 'x' },
    { key: 'current_ratio', label: 'Current Ratio', format: 'x' },
    { key: 'quick_ratio', label: 'Quick Ratio', format: 'x' },
    { key: 'altman_z', label: 'Altman Z-Score', format: 'z' },
    { key: 'cfo_to_ebitda', label: 'CFO/EBITDA', format: 'x' },
    { key: 'fcf_to_net_income', label: 'FCF/Net Income', format: 'x' },
    { key: 'revenue_cagr', label: 'Revenue CAGR', format: 'pct' },
    { key: 'operating_leverage', label: 'Operating Leverage', format: 'x' },
];

const formatValue = (value: number | undefined, format: string, altmanZone?: string) => {
    if (value === undefined || Number.isNaN(value)) {
        return 'N/A';
    }
    switch (format) {
        case 'pct':
            return `${(value * 100).toFixed(1)}%`;
        case 'x':
            return `${value.toFixed(2)}x`;
        case 'z':
            return `${value.toFixed(2)}${altmanZone ? ` (${altmanZone})` : ''}`;
        default:
            return value.toFixed(2);
    }
};

const statusColor = (status?: string) => {
    if (status === 'STRONG') return 'var(--accent-green)';
    if (status === 'CRITICAL') return 'var(--accent-red)';
    if (status === 'WEAK') return 'var(--accent-amber)';
    return 'var(--text-secondary)';
};

const MetricTable = ({ metrics, statuses, benchmarks, altmanZone }: MetricTableProps) => {
    return (
        <div className="metric-table-wrap">
            <table className="metric-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Status</th>
                        <th>Benchmark</th>
                    </tr>
                </thead>
                <tbody>
                    {METRIC_ROWS.map((row) => {
                        const value = metrics[row.key] as number | undefined;
                        const status = statuses[row.key];
                        return (
                            <tr key={row.key}>
                                <td>{row.label}</td>
                                <td>{formatValue(value, row.format, altmanZone)}</td>
                                <td style={{ color: statusColor(status) }}>{status || 'N/A'}</td>
                                <td>{benchmarks[row.key] || 'N/A'}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
            <style jsx>{`
                .metric-table-wrap {
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    overflow: hidden;
                }
                .metric-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }
                th,
                td {
                    padding: 10px 12px;
                    border-bottom: 1px solid var(--border-subtle);
                }
                th {
                    text-align: left;
                    color: var(--text-secondary);
                    background: var(--bg-surface);
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                    font-size: 10px;
                }
                tr:last-child td {
                    border-bottom: none;
                }
            `}</style>
        </div>
    );
};

export default MetricTable;
