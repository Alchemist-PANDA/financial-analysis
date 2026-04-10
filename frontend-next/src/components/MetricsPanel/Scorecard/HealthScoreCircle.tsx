import React, { useEffect, useState } from 'react';

type HealthScoreCircleProps = {
    score: number;
    band: string;
    color: string;
};

const resolveColor = (value: string) => {
    if (value === 'green') return 'var(--accent-green)';
    if (value === 'amber') return 'var(--accent-amber)';
    if (value === 'red') return 'var(--accent-red)';
    return value || 'var(--accent-blue)';
};

const HealthScoreCircle = ({ score, band, color }: HealthScoreCircleProps) => {
    const [progress, setProgress] = useState(0);
    const radius = 52;
    const circumference = 2 * Math.PI * radius;
    const clamped = Math.max(0, Math.min(score, 100));
    const offset = circumference - (progress / 100) * circumference;

    useEffect(() => {
        const timer = setTimeout(() => setProgress(clamped), 50);
        return () => clearTimeout(timer);
    }, [clamped]);

    return (
        <div className="health-score-circle">
            <svg width="140" height="140" viewBox="0 0 140 140">
                <circle
                    cx="70"
                    cy="70"
                    r={radius}
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="10"
                    fill="none"
                />
                <circle
                    cx="70"
                    cy="70"
                    r={radius}
                    stroke={resolveColor(color)}
                    strokeWidth="10"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    style={{ transition: 'stroke-dashoffset 0.4s ease-out' }}
                />
            </svg>
            <div className="score-center">
                <div className="score-value">{clamped}</div>
                <div className="score-band">{band}</div>
            </div>
            <style jsx>{`
                .health-score-circle {
                    position: relative;
                    width: 140px;
                    height: 140px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .score-center {
                    position: absolute;
                    text-align: center;
                }
                .score-value {
                    font-size: 32px;
                    font-weight: 700;
                    color: ${resolveColor(color)};
                }
                .score-band {
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    color: rgba(255,255,255,0.5);
                }
            `}</style>
        </div>
    );
};

export default HealthScoreCircle;
