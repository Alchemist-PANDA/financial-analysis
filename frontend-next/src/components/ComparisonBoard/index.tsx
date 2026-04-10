'use client';

import React, { useMemo } from 'react';
import MetricRow from './MetricRow';
import WinnerScore from './WinnerScore';

export type ComparisonYearMetric = {
    year: string;
    revenue: number;
    ebitda: number;
    net_income: number;
    ebitda_margin: number;
    net_margin: number;
    net_debt: number;
    leverage: number;
    asset_turnover: number;
    equity_multiplier: number;
    roe: number;
    dso: number;
    inventory_turnover: number;
    fcf_conversion_pct: number;
    z_score: number;
};

export type ComparisonFinancialData = {
    yearly: ComparisonYearMetric[];
    revenue_cagr_pct: number;
    revenue_trajectory: string;
    margin_signal: string;
    debt_signal: string;
    solvency_signal: string;
    current_z_score: number;
    current_roe: number;
    current_dso: number;
    current_inventory_turnover: number;
    current_fcf_conversion_pct: number;
};

type ComparisonBoardProps = {
    companyA: ComparisonFinancialData;
    companyB: ComparisonFinancialData;
    industryAverage: ComparisonFinancialData;
    companyALabel?: string;
    companyBLabel?: string;
};

type MetricDescriptor = {
    metricName: string;
    companyAValue: number;
    companyBValue: number;
    industryAverageValue: number;
    higherIsBetter?: boolean;
};

const latestYear = (data: ComparisonFinancialData) => data.yearly[data.yearly.length - 1];

const ComparisonBoard = ({
    companyA,
    companyB,
    industryAverage,
    companyALabel = 'Company A',
    companyBLabel = 'Company B',
}: ComparisonBoardProps) => {
    const rows = useMemo<MetricDescriptor[]>(() => {
        const aLatest = latestYear(companyA);
        const bLatest = latestYear(companyB);
        const iLatest = latestYear(industryAverage);

        return [
            {
                metricName: 'Revenue CAGR %',
                companyAValue: companyA.revenue_cagr_pct,
                companyBValue: companyB.revenue_cagr_pct,
                industryAverageValue: industryAverage.revenue_cagr_pct,
            },
            {
                metricName: 'Altman Z-Score',
                companyAValue: companyA.current_z_score,
                companyBValue: companyB.current_z_score,
                industryAverageValue: industryAverage.current_z_score,
            },
            {
                metricName: 'Current ROE %',
                companyAValue: companyA.current_roe,
                companyBValue: companyB.current_roe,
                industryAverageValue: industryAverage.current_roe,
            },
            {
                metricName: 'Current DSO',
                companyAValue: companyA.current_dso,
                companyBValue: companyB.current_dso,
                industryAverageValue: industryAverage.current_dso,
                higherIsBetter: false,
            },
            {
                metricName: 'Current Inventory Turnover',
                companyAValue: companyA.current_inventory_turnover,
                companyBValue: companyB.current_inventory_turnover,
                industryAverageValue: industryAverage.current_inventory_turnover,
            },
            {
                metricName: 'Current FCF Conversion %',
                companyAValue: companyA.current_fcf_conversion_pct,
                companyBValue: companyB.current_fcf_conversion_pct,
                industryAverageValue: industryAverage.current_fcf_conversion_pct,
            },
            {
                metricName: 'Latest EBITDA Margin %',
                companyAValue: aLatest?.ebitda_margin ?? 0,
                companyBValue: bLatest?.ebitda_margin ?? 0,
                industryAverageValue: iLatest?.ebitda_margin ?? 0,
            },
            {
                metricName: 'Latest Net Margin %',
                companyAValue: aLatest?.net_margin ?? 0,
                companyBValue: bLatest?.net_margin ?? 0,
                industryAverageValue: iLatest?.net_margin ?? 0,
            },
            {
                metricName: 'Latest Asset Turnover',
                companyAValue: aLatest?.asset_turnover ?? 0,
                companyBValue: bLatest?.asset_turnover ?? 0,
                industryAverageValue: iLatest?.asset_turnover ?? 0,
            },
            {
                metricName: 'Latest Z-Score',
                companyAValue: aLatest?.z_score ?? 0,
                companyBValue: bLatest?.z_score ?? 0,
                industryAverageValue: iLatest?.z_score ?? 0,
            },
        ];
    }, [companyA, companyB, industryAverage]);

    const winnerSummary = useMemo(() => {
        const beatsIndustry = (value: number, industry: number, higherIsBetter: boolean) =>
            higherIsBetter ? value >= industry : value <= industry;

        let companyAWins = 0;
        let companyBWins = 0;

        rows.forEach((row) => {
            const higherIsBetter = row.higherIsBetter ?? true;
            if (beatsIndustry(row.companyAValue, row.industryAverageValue, higherIsBetter)) {
                companyAWins += 1;
            }
            if (beatsIndustry(row.companyBValue, row.industryAverageValue, higherIsBetter)) {
                companyBWins += 1;
            }
        });

        if (companyAWins >= companyBWins) {
            return { label: companyALabel, wins: companyAWins };
        }

        return { label: companyBLabel, wins: companyBWins };
    }, [rows, companyALabel, companyBLabel]);

    return (
        <section className="comparison-board">
            <div className="comparison-header">
                <div className="metric-head">Metric</div>
                <div className="company-head">{companyALabel}</div>
                <div className="company-head">{companyBLabel}</div>
                <div className="company-head">Industry Avg</div>
            </div>

            {rows.map((row) => (
                <MetricRow
                    key={row.metricName}
                    metricName={row.metricName}
                    companyAValue={row.companyAValue}
                    companyBValue={row.companyBValue}
                    industryAverageValue={row.industryAverageValue}
                    higherIsBetter={row.higherIsBetter}
                />
            ))}

            <div className="winner-wrap">
                <WinnerScore companyLabel={winnerSummary.label} strongerMetricCount={winnerSummary.wins} totalMetrics={50} />
            </div>

            <style jsx>{`
                .comparison-board {
                    border: 1px solid var(--border);
                    background: var(--bg-surface);
                    box-shadow: var(--shadow-card);
                    overflow-x: auto;
                }

                .comparison-header {
                    display: grid;
                    grid-template-columns: 220px 180px 180px 180px;
                    border-bottom: 1px solid var(--border);
                    background: var(--bg-elevated);
                }

                .metric-head,
                .company-head {
                    padding: 10px 12px;
                    font-size: 12px;
                    color: var(--text-muted);
                    border-right: 1px solid var(--border);
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }

                .company-head:last-child {
                    border-right: none;
                }

                .winner-wrap {
                    padding: 16px;
                }
            `}</style>
        </section>
    );
};

export default ComparisonBoard;
