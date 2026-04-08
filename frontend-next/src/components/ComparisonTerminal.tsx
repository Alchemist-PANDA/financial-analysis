'use client';
import React, { useState } from 'react';
import MainTerminal from './MainTerminal';

const ComparisonTerminal = () => {
    const [tickerA, setTickerA] = useState('MSFT');
    const [tickerB, setTickerB] = useState('INTC');
    const [comparisonResult, setComparisonResult] = useState<string | null>(null);

    const generateComparisonAI = (dataA: any, dataB: any) => {
        // Simple logic for comparison summary
        const winA = dataA.metrics.current_z_score > dataB.metrics.current_z_score;
        const msg = winA 
            ? `${tickerA} holds a superior solvency profile (Altman-Z: ${dataA.metrics.current_z_score}). ${tickerB} shows higher leverage risk.`
            : `${tickerB} holds a superior solvency profile (Altman-Z: ${dataB.metrics.current_z_score}). ${tickerA} shows higher leverage risk.`;
        setComparisonResult(`COMPARISON VERDICT: ${msg}`);
    };

    return (
        <div className="comparison-container">
            <div className="comparison-grid">
                <div className="comparison-pane">
                    <MainTerminal forceTicker={tickerA} />
                </div>
                <div className="comparison-pane">
                    <MainTerminal forceTicker={tickerB} />
                </div>
            </div>
            {comparisonResult && (
                <div className="comparison-verdict-bar">
                    <span className="grid-label" style={{ color: 'var(--primary)' }}>⚡ AI COMPARISON</span>
                    <p style={{ margin: 0, fontSize: '13px' }}>{comparisonResult}</p>
                </div>
            )}

            <style jsx>{`
                .comparison-container {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                    overflow: hidden;
                    background: #000;
                }
                .comparison-grid {
                    flex: 1;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1px;
                    background: var(--border);
                }
                .comparison-pane {
                    background: #000;
                    overflow: hidden;
                }
                .comparison-verdict-bar {
                    padding: 16px 24px;
                    background: #050505;
                    border-top: 1px solid var(--primary);
                    display: flex;
                    align-items: center;
                    gap: 24px;
                }
            `}</style>
        </div>
    );
};

export default ComparisonTerminal;
