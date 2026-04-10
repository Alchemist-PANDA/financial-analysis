import React from 'react';
import type { ScorecardMetric } from './types';

type StrengthsRisksPanelProps = {
    strengths: ScorecardMetric[];
    risks: ScorecardMetric[];
    criticalAlerts: string[];
    debtMaturityWall: boolean;
};

const StrengthsRisksPanel = ({
    strengths,
    risks,
    criticalAlerts,
    debtMaturityWall,
}: StrengthsRisksPanelProps) => {
    return (
        <div className="strengths-risks">
            <div className="column">
                <div className="column-title">Strengths</div>
                {strengths.length === 0 && <div className="empty">No standout strengths.</div>}
                {strengths.map((item, index) => (
                    <div key={`${item.metric}-${index}`} className="row strength">
                        * {item.metric} - {item.value.toFixed(2)}
                    </div>
                ))}
            </div>
            <div className="column">
                <div className="column-title">Risks</div>
                {risks.length === 0 && <div className="empty">No material risks flagged.</div>}
                {risks.map((item, index) => (
                    <div
                        key={`${item.metric}-${index}`}
                        className={`row risk ${item.status === 'CRITICAL' ? 'critical' : ''}`}
                    >
                        {item.status === 'CRITICAL' ? '!' : '^'} {item.metric} - {item.value.toFixed(2)}
                    </div>
                ))}
            </div>

            {(criticalAlerts.length > 0 || debtMaturityWall) && (
                <div className="alert-banner">
                    {debtMaturityWall && (
                        <div className="alert-line">
                            WARNING: DEBT MATURITY WALL DETECTED - Immediate refinancing risk
                        </div>
                    )}
                    {criticalAlerts.map((alert, index) => (
                        <div key={`${alert}-${index}`} className="alert-line">
                            {alert}
                        </div>
                    ))}
                </div>
            )}

            <style jsx>{`
                .strengths-risks {
                    display: grid;
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 16px;
                }
                .column {
                    background: var(--bg-surface);
                    border: 1px solid var(--border-subtle);
                    padding: 12px;
                    border-radius: var(--radius-md);
                }
                .column-title {
                    text-transform: uppercase;
                    font-size: 11px;
                    letter-spacing: 0.08em;
                    color: var(--text-secondary);
                    margin-bottom: 8px;
                }
                .row {
                    font-size: 12px;
                    margin-bottom: 6px;
                }
                .strength {
                    color: var(--accent-green);
                }
                .risk {
                    color: var(--accent-amber);
                }
                .risk.critical {
                    color: var(--accent-red);
                }
                .empty {
                    font-size: 11px;
                    color: var(--text-muted);
                }
                .alert-banner {
                    grid-column: 1 / -1;
                    margin-top: 8px;
                    padding: 10px 12px;
                    border: 1px solid #FED7AA;
                    border-left: 3px solid #F97316;
                    background: #FFF7ED;
                    color: #C2410C;
                    font-size: 11px;
                    font-weight: 600;
                }
                .alert-line + .alert-line {
                    margin-top: 4px;
                }
            `}</style>
        </div>
    );
};

export default StrengthsRisksPanel;
