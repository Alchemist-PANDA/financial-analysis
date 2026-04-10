export type ScorecardMetric = {
    metric: string;
    value: number;
    status: string;
};

export type ScorecardResult = {
    analysis_id?: number;
    company_name: string;
    timestamp: string;
    scoring_mode: 'credit' | 'investment';
    scoring_model_version: string;
    confidence_label: string;
    health_score: number;
    health_band: string;
    health_color: string;
    sub_scores: Record<string, number>;
    sub_score_breakdowns: Record<string, Record<string, number>>;
    top_strengths: ScorecardMetric[];
    top_risks: ScorecardMetric[];
    critical_alerts: string[];
    debt_maturity_wall: boolean;
    metric_statuses: Record<string, string>;
    metric_benchmarks: Record<string, string>;
    metrics: Record<string, number | Record<string, number> | undefined>;
    altman_z_full?: {
        z_score: number;
        zone: string;
        x1: number;
        x2: number;
        x3: number;
        x4: number;
        x5: number;
    };
    narrative?: string;
    narrative_error?: string;
    inputs?: Record<string, unknown>;
};
