'use client';

import React from 'react';

type MetricRowProps = {
    metricName: string;
    companyAValue: number;
    companyBValue: number;
    industryAverageValue: number;
    higherIsBetter?: boolean;
};

const formatValue = (value: number | undefined | null, suffix = '', precision = 2) => {
    if (value === undefined || value === null || !Number.isFinite(value)) {
        return '';
    }
    return `${value.toFixed(precision)}${suffix}`;
};

const MetricRow = ({
    metricName,
    companyAValue,
    companyBValue,
    industryAverageValue,
    higherIsBetter = true,
}: MetricRowProps) => {
    const isMissing = (val: number | undefined | null) => {
        const formatted = formatValue(val);
        return !formatted || formatted === '0.00' || formatted === '0.0' || formatted === '--';
    };
    if (isMissing(companyAValue) && isMissing(companyBValue) && isMissing(industryAverageValue)) {
        return null;
    }
    const beatsIndustry = (value: number) => {
        if (!Number.isFinite(value) || !Number.isFinite(industryAverageValue)) {
            return false;
        }
        return higherIsBetter ? value >= industryAverageValue : value <= industryAverageValue;
    };

    const companyAClass = beatsIndustry(companyAValue) ? 'cell-win' : 'cell-loss';
    const companyBClass = beatsIndustry(companyBValue) ? 'cell-win' : 'cell-loss';

    return (
        <div className="metric-row">
            <div className="metric-cell metric-name">{metricName}</div>
            <div className={`metric-cell ${companyAClass}`}>{formatValue(companyAValue)}</div>
            <div className={`metric-cell ${companyBClass}`}>{formatValue(companyBValue)}</div>
            <div className="metric-cell industry-cell">{formatValue(industryAverageValue)}</div>

            <style jsx>{`
                .metric-row {
                    display: grid;
                    grid-template-columns: 220px 180px 180px 180px;
                    border-bottom: 1px solid var(--border);
                }

                .metric-cell {
                    padding: 10px 12px;
                    font-family: var(--font-mono);
                    font-size: 12px;
                    border-right: 1px solid var(--border);
                }

                .metric-cell:last-child {
                    border-right: none;
                }

                .metric-name {
                    color: var(--foreground);
                    background: var(--bg-elevated);
                    font-family: var(--font-sans);
                    font-size: 13px;
                }

                .cell-win {
                    color: #15803D;
                    background: #DCFCE7;
                }

                .cell-loss {
                    color: #B91C1C;
                    background: #FEE2E2;
                }

                .industry-cell {
                    color: var(--text-muted);
                    background: var(--bg-elevated);
                }
            `}</style>
        </div>
    );
};

export default MetricRow;
