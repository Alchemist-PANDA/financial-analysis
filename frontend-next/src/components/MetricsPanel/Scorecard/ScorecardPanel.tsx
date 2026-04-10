import React from 'react';
import type { ScorecardResult } from './types';
import HealthScoreCircle from './HealthScoreCircle';
import SubScoreBars from './SubScoreBars';
import StrengthsRisksPanel from './StrengthsRisksPanel';
import MetricTable from './MetricTable';
import AltmanZGauge from './AltmanZGauge';
import NarrativePanel from './NarrativePanel';
import ModeToggle from './ModeToggle';
import ViewToggle from './ViewToggle';
import ExportBar from './ExportBar';

type ScorecardPanelProps = {
    result: ScorecardResult;
    view: 'simple' | 'expert';
    mode: 'credit' | 'investment';
    onModeChange: (mode: 'credit' | 'investment') => void;
    onViewChange: (view: 'simple' | 'expert') => void;
};

const ScorecardPanel = ({ result, view, mode, onModeChange, onViewChange }: ScorecardPanelProps) => {
    return (
        <div className="scorecard-panel">
            <div className="scorecard-controls">
                <ModeToggle mode={mode} onChange={onModeChange} />
                <ViewToggle view={view} onChange={onViewChange} />
            </div>

            <div className="scorecard-header">
                <HealthScoreCircle
                    score={result.health_score}
                    band={result.health_band}
                    color={result.health_color}
                />
                <div className="scorecard-summary">
                    <StrengthsRisksPanel
                        strengths={result.top_strengths}
                        risks={result.top_risks}
                        criticalAlerts={result.critical_alerts}
                        debtMaturityWall={result.debt_maturity_wall}
                    />
                </div>
            </div>

            <NarrativePanel
                narrative={result.narrative || 'Narrative pending.'}
                color={result.health_color}
                confidenceLabel={result.confidence_label}
                modelVersion={result.scoring_model_version}
            />

            {view === 'expert' && (
                <>
                    <SubScoreBars subScores={result.sub_scores} mode={mode} />
                    <MetricTable
                        metrics={result.metrics}
                        statuses={result.metric_statuses}
                        benchmarks={result.metric_benchmarks}
                        altmanZone={result.altman_z_full?.zone}
                    />
                    <AltmanZGauge
                        zScore={result.altman_z_full?.z_score || 0}
                        zone={result.altman_z_full?.zone || 'Unknown'}
                        components={
                            result.altman_z_full
                                ? {
                                    x1: result.altman_z_full.x1,
                                    x2: result.altman_z_full.x2,
                                    x3: result.altman_z_full.x3,
                                    x4: result.altman_z_full.x4,
                                    x5: result.altman_z_full.x5,
                                }
                                : undefined
                        }
                    />
                    <details className="breakdown">
                        <summary>Sub-score breakdown</summary>
                        <pre>{JSON.stringify(result.sub_score_breakdowns, null, 2)}</pre>
                    </details>
                    <details className="breakdown">
                        <summary>Raw inputs</summary>
                        <pre>{JSON.stringify(result.inputs || {}, null, 2)}</pre>
                    </details>
                </>
            )}

            <ExportBar result={result} />

            <style jsx>{`
                .scorecard-panel {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                .scorecard-controls {
                    display: flex;
                    justify-content: space-between;
                    gap: 12px;
                }
                .scorecard-header {
                    display: grid;
                    grid-template-columns: 160px 1fr;
                    gap: 16px;
                    align-items: start;
                    background: linear-gradient(135deg,#0F172A 0%,#1E293B 50%,#0F172A 100%);
                    border: 1px solid #CBD5E1;
                }
                .scorecard-summary {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                .breakdown {
                    background: var(--bg-surface);
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    padding: 12px;
                    font-size: 11px;
                    color: var(--text-secondary);
                }
                .breakdown pre {
                    white-space: pre-wrap;
                    font-size: 10px;
                    color: var(--text-primary);
                }
            `}</style>
        </div>
    );
};

export default ScorecardPanel;
