'use client';

import Sidebar from "@/components/Sidebar";
import MainTerminal, { type MetricsPayload as TerminalMetricsPayload } from "@/components/MainTerminal";
import { useState } from "react";

import ComparisonTerminal from "@/components/ComparisonTerminal";
import MetricsPanel, { type FinancialData } from "@/components/MetricsPanel";
import ComparisonBoard from "@/components/ComparisonBoard";
import { FEATURES } from "@/config/features";

const EMPTY_FINANCIAL_DATA: FinancialData = {
  yearly: [
    {
      year: 'Y0',
      revenue: 0,
      ebitda: 0,
      net_income: 0,
      ebitda_margin: 0,
      net_margin: 0,
      net_debt: 0,
      leverage: 0,
      asset_turnover: 0,
      equity_multiplier: 0,
      roe: 0,
      dso: 0,
      inventory_turnover: 0,
      fcf_conversion_pct: 0,
      z_score: 0,
      roa: 0,
      gross_margin: 0,
      debt_equity: 0,
      current_ratio: 0,
      quick_ratio: 0,
      cash_ratio: 0,
      interest_coverage: 0,
      pe_ratio: 0,
      pb_ratio: 0,
      ev_ebitda: 0,
    },
  ],
  revenue_cagr_pct: 0,
  revenue_trajectory: 'STEADY',
  margin_signal: 'STABLE',
  debt_signal: 'STABLE',
  solvency_signal: 'GREY_ZONE',
  current_z_score: 0,
  current_roe: 0,
  current_roa: 0,
  current_gross_margin: 0,
  current_debt_equity: 0,
  current_ratio: 0,
  current_quick_ratio: 0,
  current_cash_ratio: 0,
  current_interest_coverage: 0,
  current_pe_ratio: 0,
  current_pb_ratio: 0,
  current_ev_ebitda: 0,
  current_dso: 0,
  current_inventory_turnover: 0,
  current_fcf_conversion_pct: 0,
};

export default function Home() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [currentView, setCurrentView] = useState<'live' | 'compare'>('live');
  const [financialData, setFinancialData] = useState<FinancialData | null>(null);

  const handleAnalysisComplete = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDataLoaded = (data: TerminalMetricsPayload) => {
    // Map backend metrics to dashboard props
    // This provides a consistent bridge between the streaming terminal and static panels
    const mappedYearly: FinancialData["yearly"] = (data.yearly || []).map((year) => ({
      year: year.year,
      revenue: year.revenue ?? 0,
      ebitda: 0,
      net_income: 0,
      ebitda_margin: year.ebitda_margin ?? 0,
      net_margin: 0,
      net_debt: 0,
      leverage: 0,
      asset_turnover: year.asset_turnover ?? 0,
      equity_multiplier: 0,
      roe: year.roe ?? 0,
      dso: year.dso ?? 0,
      inventory_turnover: year.inventory_turnover ?? 0,
      fcf_conversion_pct: year.fcf_conversion_pct ?? 0,
      z_score: year.z_score ?? 0,
      roa: 0,
      gross_margin: 0,
      debt_equity: 0,
      current_ratio: 0,
      quick_ratio: 0,
      cash_ratio: 0,
      interest_coverage: 0,
      pe_ratio: 0,
      pb_ratio: 0,
      ev_ebitda: 0,
    }));

    setFinancialData({
      ...EMPTY_FINANCIAL_DATA,
      yearly: mappedYearly.length ? mappedYearly : EMPTY_FINANCIAL_DATA.yearly,
      revenue_cagr_pct: data.revenue_cagr_pct ?? 0,
      margin_signal: data.margin_signal ?? "STABLE",
      solvency_signal: data.solvency_signal ?? "GREY_ZONE",
      current_roe: data.yearly?.[0]?.roe ?? 0,
      current_dso: data.yearly?.[0]?.dso ?? 0,
      current_z_score: data.current_z_score ?? 0,
      current_fcf_conversion_pct: data.current_fcf_conversion_pct ?? 0,
    });
  };

  return (
    <div className="terminal-main">
      <Sidebar
        onSelectTicker={(t) => { setSelectedTicker(t); setCurrentView('live'); }}
        refreshTrigger={refreshTrigger}
        currentView={currentView}
        onViewChange={setCurrentView}
      />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflowY: 'auto' }}>
        <div style={{ flexShrink: 0 }}>
          {currentView === 'live' ? (
            <MainTerminal
              forceTicker={selectedTicker}
              onAnalysisComplete={handleAnalysisComplete}
              onDataLoaded={handleDataLoaded}
            />
          ) : (
            <ComparisonTerminal />
          )}
        </div>

        {FEATURES.METRICS_PANEL && financialData && currentView === 'live' && (
          <div style={{ padding: '16px', borderTop: '1px solid var(--border)', background: 'var(--background)' }}>
            <h3 className="grid-label" style={{ marginBottom: '16px', color: 'var(--primary)' }}>
              Forensic Health Dashboard: {selectedTicker}
            </h3>
            <MetricsPanel financialData={financialData} />
          </div>
        )}

        {FEATURES.COMPARISON_BOARD && currentView === 'compare' && (
          <div style={{ padding: '16px', borderTop: '1px solid var(--border)', background: 'var(--background)' }}>
            <ComparisonBoard
              companyA={financialData || EMPTY_FINANCIAL_DATA}
              companyB={EMPTY_FINANCIAL_DATA}
              industryAverage={EMPTY_FINANCIAL_DATA}
              companyALabel={selectedTicker || "Company A"}
              companyBLabel="Target B"
            />
          </div>
        )}
      </div>
    </div>
  );
}
