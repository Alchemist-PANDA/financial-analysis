import React from 'react';
import HealthScoreCircle from '@/components/MetricsPanel/Scorecard/HealthScoreCircle';
import type { ScorecardResult } from '@/components/MetricsPanel/Scorecard/types';

type ScorecardComparisonProps = {
    left: ScorecardResult;
    right: ScorecardResult;
};

const METRICS = [
    { key: 'roic', label: 'ROIC', invert: false },
    { key: 'ebit_margin', label: 'EBIT Margin', invert: false },
    { key: 'net_debt_to_ebitda', label: 'Net Debt/EBITDA', invert: true },
    { key: 'interest_coverage', label: 'Interest Coverage', invert: false },
    { key: 'current_ratio', label: 'Current Ratio', invert: false },
    { key: 'quick_ratio', label: 'Quick Ratio', invert: false },
    { key: 'altman_z', label: 'Altman Z', invert: false },
    { key: 'revenue_cagr', label: 'Revenue CAGR', invert: false },
];

const formatMetric = (key: string, value: number | undefined) => {
    if (value === undefined || Number.isNaN(value)) return 'N/A';
    if (key.endsWith('cagr') || key.includes('margin') || key === 'roic') {
        return `${(value * 100).toFixed(1)}%`;
    }
    if (key.includes('ratio') || key.includes('coverage') || key.includes('ebitda') || key.includes('leverage')) {
        return `${value.toFixed(2)}x`;
    }
    return value.toFixed(2);
};

const ScorecardComparison = ({ left, right }: ScorecardComparisonProps) => {
    return (
        <div className="scorecard-compare">
            <div className="score-row">
                <HealthScoreCircle score={left.health_score} band={left.health_band} color={left.health_color} />
                <HealthScoreCircle score={right.health_score} band={right.health_band} color={right.health_color} />
            </div>
            <table className="compare-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>{left.company_name}</th>
                        <th>{right.company_name}</th>
                        <th>Better</th>
                    </tr>
                </thead>
                <tbody>
                    {METRICS.map((metric) => {
                        const leftValue = left.metrics[metric.key] as number | undefined;
                        const rightValue = right.metrics[metric.key] as number | undefined;
                        const leftBetter = metric.invert
                            ? (leftValue ?? 0) <= (rightValue ?? 0)
                            : (leftValue ?? 0) >= (rightValue ?? 0);
                        const betterName = leftBetter ? left.company_name : right.company_name;

                        return (
                            <tr key={metric.key}>
                                <td>{metric.label}</td>
                                <td style={{ color: leftBetter ? 'var(--accent-green)' : undefined }}>
                                    {formatMetric(metric.key, leftValue)}
                                </td>
                                <td style={{ color: !leftBetter ? 'var(--accent-green)' : undefined }}>
                                    {formatMetric(metric.key, rightValue)}
                                </td>
                                <td>{betterName}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
            <style jsx>{`
                .scorecard-compare {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                .score-row {
                    display: grid;
                    grid-template-columns: repeat(2, 160px);
                    gap: 16px;
                }
                .compare-table {
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
                    font-size: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }
            `}</style>
        </div>
    );
};

export default ScorecardComparison;
