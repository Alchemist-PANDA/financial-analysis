import React, { useState } from 'react';

type AltmanZGaugeProps = {
    zScore: number;
    zone: string;
    components?: { x1: number; x2: number; x3: number; x4: number; x5: number };
};

const AltmanZGauge = ({ zScore, zone, components }: AltmanZGaugeProps) => {
    const [expanded, setExpanded] = useState(false);
    const clamped = Math.max(0, Math.min(zScore, 4));
    const position = (clamped / 4) * 100;

    return (
        <div className="altman-gauge">
            <div className="gauge-header">
                <span>Altman Z-Score</span>
                <button className="toggle" onClick={() => setExpanded(!expanded)}>
                    {expanded ? 'Hide X1-X5' : 'Show X1-X5'}
                </button>
            </div>
            <div className="gauge-bar">
                <div className="zone distress">Distress</div>
                <div className="zone grey">Grey</div>
                <div className="zone safe">Safe</div>
                <div className="marker" style={{ left: `${position}%` }} />
            </div>
            <div className="gauge-footer">
                <strong>{zScore.toFixed(2)}</strong> ({zone})
            </div>
            {expanded && components && (
                <div className="components">
                    <div>X1: {components.x1.toFixed(2)}</div>
                    <div>X2: {components.x2.toFixed(2)}</div>
                    <div>X3: {components.x3.toFixed(2)}</div>
                    <div>X4: {components.x4.toFixed(2)}</div>
                    <div>X5: {components.x5.toFixed(2)}</div>
                </div>
            )}
            <style jsx>{`
                .altman-gauge {
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    padding: 12px;
                    background: var(--bg-surface);
                }
                .gauge-header {
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: var(--text-secondary);
                    margin-bottom: 8px;
                }
                .toggle {
                    background: none;
                    border: none;
                    color: var(--accent-blue);
                    font-size: 11px;
                    cursor: pointer;
                }
                .gauge-bar {
                    position: relative;
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    height: 12px;
                    border-radius: 6px;
                    overflow: hidden;
                }
                .zone {
                    font-size: 9px;
                    text-align: center;
                    line-height: 12px;
                    color: #0F172A;
                }
                .distress { background: var(--accent-red); }
                .grey { background: var(--accent-amber); }
                .safe { background: var(--accent-green); }
                .marker {
                    position: absolute;
                    top: -2px;
                    width: 2px;
                    height: 16px;
                    background: #0F172A;
                }
                .gauge-footer {
                    margin-top: 8px;
                    font-size: 12px;
                }
                .components {
                    margin-top: 10px;
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 6px;
                    font-size: 11px;
                    color: var(--text-secondary);
                }
            `}</style>
        </div>
    );
};

export default AltmanZGauge;
