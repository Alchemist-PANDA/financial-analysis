import React from 'react';
import * as XLSX from 'xlsx';
import { jsPDF } from 'jspdf';
import type { ScorecardResult } from './types';

type ExportBarProps = {
    result: ScorecardResult;
};

const ExportBar = ({ result }: ExportBarProps) => {
    const handleExcel = () => {
        const wb = XLSX.utils.book_new();

        const summaryData = [
            ['Company', result.company_name],
            ['Health Score', result.health_score],
            ['Health Band', result.health_band],
            ['Scoring Mode', result.scoring_mode],
            ['Data Confidence', result.confidence_label],
            ['Model Version', result.scoring_model_version],
            ['Generated', result.timestamp],
            [],
            ['SUB-SCORES', ''],
            ['Business Quality', result.sub_scores.business_quality],
            ['Cash Flow', result.sub_scores.cash_flow],
            ['Safety', result.sub_scores.safety],
            ['Growth', result.sub_scores.growth],
            ['Valuation', result.sub_scores.valuation],
        ];
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summaryData), 'Summary');

        const metricsRows = Object.entries(result.metrics).map(([k, v]) => [
            k,
            typeof v === 'number' ? v : JSON.stringify(v),
        ]);
        metricsRows.unshift(['METRIC', 'VALUE']);
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(metricsRows), 'Metrics');

        const inputRows = Object.entries(result.inputs || {}).map(([k, v]) => [
            k,
            typeof v === 'number' ? v : JSON.stringify(v),
        ]);
        inputRows.unshift(['INPUT', 'VALUE ($M)']);
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(inputRows), 'Inputs');

        const filename = `apex-${result.company_name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.xlsx`;
        XLSX.writeFile(wb, filename);
    };

    const handlePdf = () => {
        const doc = new jsPDF();
        doc.setFont('helvetica', 'bold');
        doc.text(`Apex Scorecard Report`, 14, 16);
        doc.setFont('helvetica', 'normal');
        doc.text(`Company: ${result.company_name}`, 14, 26);
        doc.text(`Score: ${result.health_score} (${result.health_band})`, 14, 34);
        doc.text(`Mode: ${result.scoring_mode}`, 14, 42);
        doc.text(`Model: ${result.scoring_model_version}`, 14, 50);
        doc.text(`Generated: ${result.timestamp}`, 14, 58);

        doc.addPage();
        doc.setFont('helvetica', 'bold');
        doc.text('Key Metrics', 14, 16);
        doc.setFont('helvetica', 'normal');

        let y = 28;
        Object.entries(result.metrics).forEach(([key, value]) => {
            if (y > 280) {
                doc.addPage();
                y = 20;
            }
            doc.text(`${key}: ${typeof value === 'number' ? value.toFixed(4) : ''}`, 14, y);
            y += 8;
        });

        const filename = `apex-${result.company_name.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.pdf`;
        doc.save(filename);
    };

    return (
        <div className="export-bar">
            <button className="export-btn" onClick={handlePdf}>
                PDF REPORT
            </button>
            <button className="export-btn" onClick={handleExcel}>
                EXCEL EXPORT
            </button>
            <style jsx>{`
                .export-bar {
                    display: flex;
                    gap: 12px;
                }
                .export-btn {
                    flex: 1;
                    background: var(--bg-surface);
                    border: 1px solid var(--border-subtle);
                    color: var(--text-primary);
                    font-size: 11px;
                    text-transform: uppercase;
                    padding: 8px 12px;
                    cursor: pointer;
                }
            `}</style>
        </div>
    );
};

export default ExportBar;
