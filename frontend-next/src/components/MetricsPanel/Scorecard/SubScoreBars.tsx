import React from 'react';

type SubScoreBarsProps = {
    subScores: Record<string, number>;
    mode: string;
};

const PILLARS = [
    { key: 'business_quality', label: 'Business Quality', max: 25 },
    { key: 'cash_flow', label: 'Cash Flow', max: 20 },
    { key: 'safety', label: 'Safety', max: 25 },
    { key: 'growth', label: 'Growth', max: 15 },
    { key: 'valuation', label: 'Valuation', max: 15 },
];

const scoreColor = (ratio: number) => {
    if (ratio >= 0.75) return 'var(--accent-green)';
    if (ratio >= 0.5) return 'var(--accent-amber)';
    return 'var(--accent-red)';
};

const SubScoreBars = ({ subScores, mode }: SubScoreBarsProps) => {
    const rows = PILLARS.filter((pillar) => !(mode === 'credit' && pillar.key === 'valuation'));

    return (
        <div className="subscore-bars">
            {rows.map((pillar, index) => {
                const score = subScores[pillar.key] ?? 0;
                const ratio = pillar.max > 0 ? score / pillar.max : 0;
                return (
                    <div className="bar-row" key={pillar.key} style={{ animationDelay: `${index * 0.08}s` }}>
                        <div className="bar-label">{pillar.label}</div>
                        <div className="bar-track">
                            <div
                                className="bar-fill"
                                style={{
                                    width: `${Math.min(ratio * 100, 100)}%`,
                                    background: scoreColor(ratio),
                                }}
                            />
                        </div>
                        <div className="bar-score">
                            {score.toFixed(1)}/{pillar.max}
                        </div>
                    </div>
                );
            })}
            <style jsx>{`
                .subscore-bars {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                .bar-row {
                    display: grid;
                    grid-template-columns: 140px 1fr 70px;
                    align-items: center;
                    gap: 12px;
                    opacity: 0;
                    animation: fadeIn 0.3s ease forwards;
                }
                .bar-label {
                    font-size: 12px;
                    color: var(--text-secondary);
                }
                .bar-track {
                    height: 8px;
                    background: var(--bg-elevated);
                    border-radius: 6px;
                    overflow: hidden;
                }
                .bar-fill {
                    height: 100%;
                    transition: width 0.3s ease;
                }
                .bar-score {
                    font-family: var(--font-mono);
                    font-size: 11px;
                    color: var(--text-primary);
                    text-align: right;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateX(-8px); }
                    to { opacity: 1; transform: translateX(0); }
                }
            `}</style>
        </div>
    );
};

export default SubScoreBars;
