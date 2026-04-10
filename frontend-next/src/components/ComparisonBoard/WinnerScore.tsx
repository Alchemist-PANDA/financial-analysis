'use client';

import React from 'react';

type WinnerScoreProps = {
    companyLabel: string;
    strongerMetricCount: number;
    totalMetrics?: number;
};

const WinnerScore = ({ companyLabel, strongerMetricCount, totalMetrics = 50 }: WinnerScoreProps) => {
    return (
        <div className="winner-score">
            <span className="grid-label">Winner Score</span>
            <div className="winner-text">{companyLabel} stronger on {strongerMetricCount}/{totalMetrics} metrics</div>

            <style jsx>{`
                .winner-score {
                    padding: 12px 16px;
                    border: 1px solid #DBEAFE;
                    background: #EFF6FF;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .winner-text {
                    color: var(--foreground);
                    font-size: 13px;
                    font-family: var(--font-mono);
                }
            `}</style>
        </div>
    );
};

export default WinnerScore;
