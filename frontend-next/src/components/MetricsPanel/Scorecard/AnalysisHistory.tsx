import React from 'react';
import type { ScorecardResult } from './types';

export type ScorecardHistoryItem = {
    id: number;
    company_name: string;
    health_score: number;
    health_band: string;
    scoring_mode: string;
    scoring_model_version: string;
    created_at: string;
    result: ScorecardResult;
    inputs: Record<string, unknown>;
};

type AnalysisHistoryProps = {
    items: ScorecardHistoryItem[];
    onSelect: (item: ScorecardHistoryItem) => void;
    onRecalculate: (item: ScorecardHistoryItem) => void;
};

const AnalysisHistory = ({ items, onSelect, onRecalculate }: AnalysisHistoryProps) => {
    return (
        <div className="history-panel">
            <div className="history-header">Analysis History</div>
            {items.length === 0 && <div className="empty">No scorecard history yet.</div>}
            {items.map((item) => (
                <div key={item.id} className="history-row">
                    <button className="history-main" onClick={() => onSelect(item)}>
                        <div className="name">{item.company_name}</div>
                        <div className="meta">
                            {item.health_score} • {item.health_band} • {item.scoring_mode} • v{item.scoring_model_version}
                        </div>
                    </button>
                    <button className="recalc" onClick={() => onRecalculate(item)}>
                        Reload & Recalculate
                    </button>
                </div>
            ))}
            <style jsx>{`
                .history-panel {
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    padding: 12px;
                    background: var(--bg-surface);
                }
                .history-header {
                    font-size: 11px;
                    color: var(--text-secondary);
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    margin-bottom: 8px;
                }
                .history-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 12px;
                    padding: 8px 0;
                    border-bottom: 1px solid var(--border-subtle);
                }
                .history-row:last-child {
                    border-bottom: none;
                }
                .history-main {
                    flex: 1;
                    background: none;
                    border: none;
                    text-align: left;
                    color: var(--text-primary);
                    cursor: pointer;
                }
                .name {
                    font-size: 12px;
                    font-weight: 600;
                }
                .meta {
                    font-size: 10px;
                    color: var(--text-secondary);
                    margin-top: 2px;
                }
                .recalc {
                    background: transparent;
                    border: 1px solid var(--border-subtle);
                    color: var(--text-secondary);
                    font-size: 10px;
                    text-transform: uppercase;
                    padding: 6px 8px;
                    cursor: pointer;
                }
                .empty {
                    font-size: 11px;
                    color: var(--text-muted);
                }
            `}</style>
        </div>
    );
};

export default AnalysisHistory;
