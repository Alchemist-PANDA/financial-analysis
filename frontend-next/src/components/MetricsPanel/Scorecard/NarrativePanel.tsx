import React from 'react';

type NarrativePanelProps = {
    narrative: string;
    color: string;
    confidenceLabel: string;
    modelVersion: string;
};

const resolveColor = (value: string) => {
    if (value === 'green') return 'var(--accent-green)';
    if (value === 'amber') return 'var(--accent-amber)';
    if (value === 'red') return 'var(--accent-red)';
    return value || 'var(--accent-blue)';
};

const NarrativePanel = ({ narrative, color, confidenceLabel, modelVersion }: NarrativePanelProps) => {
    return (
        <div className="narrative-panel" style={{ borderLeftColor: resolveColor(color) }}>
            <div className="narrative-header">
                <span className="confidence">{confidenceLabel}</span>
            </div>
            <pre className="narrative-text">{narrative || 'Narrative pending.'}</pre>
            <div className="model-version">Model {modelVersion}</div>
            <style jsx>{`
                .narrative-panel {
                    background: var(--bg-surface);
                    border-left: 3px solid;
                    padding: 16px;
                    border-radius: var(--radius-md);
                    font-family: var(--font-mono);
                }
                .narrative-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                }
                .confidence {
                    font-size: 10px;
                    text-transform: uppercase;
                    color: var(--accent-amber);
                }
                .narrative-text {
                    white-space: pre-wrap;
                    font-size: 12px;
                    color: var(--text-primary);
                    margin: 0;
                }
                .model-version {
                    margin-top: 12px;
                    font-size: 10px;
                    color: var(--text-secondary);
                    text-align: right;
                }
            `}</style>
        </div>
    );
};

export default NarrativePanel;
