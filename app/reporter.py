"""
reporter.py — Generates a professional, branded PDF report for institutional analysis.
Uses ReportLab for high-fidelity layouts.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

class FinancialReportBuilder:
    def __init__(self, ticker: str, company_name: str, analysis_data: dict):
        self.ticker = ticker.upper()
        self.company_name = company_name
        self.analysis_data = analysis_data
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configure institutional-grade typography."""
        self.styles.add(ParagraphStyle(
            name='InstitutionalHeader',
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            textTransform='uppercase',
            letterSpacing=1,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='VerdictHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=16,
            textColor=colors.HexColor("#0ea5e9"),
            spaceBefore=20,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='BodyCopy',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            alignment=0 # Left
        ))
        self.styles.add(ParagraphStyle(
            name='Tagline',
            fontName='Helvetica-Oblique',
            fontSize=9,
            textColor=colors.grey,
            alignment=2 # Right
        ))

    def generate(self) -> io.BytesIO:
        """Build the PDF and return as a byte buffer."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=LETTER,
            rightMargin=50, leftMargin=50,
            topMargin=50, bottomMargin=50
        )

        elements = []
        
        # ── HEADER ────────────────────────────────────────────────────────────
        elements.append(Paragraph("PRIVATE EQUITY RESEARCH TERMINAL", self.styles['Tagline']))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(f"{self.company_name} ({self.ticker})", self.styles['InstitutionalHeader']))
        elements.append(Paragraph(f"INSTITUTIONAL TREND ANALYSIS • {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['SubHeader']))
        elements.append(Spacer(1, 0.3 * inch))

        # ── EXTRACT DATA SAFELY ───────────────────────────────────────────────
        # Handle both nested and flat state formats
        raw_result = self.analysis_data.get("analysis_result")
        if isinstance(raw_result, dict):
            analysis = raw_result.get("analysis", {})
        else:
            analysis = self.analysis_data.get("analysis", {})
            
        metrics = self.analysis_data.get("metrics", {})
        
        # ── VERDICT SECTION ───────────────────────────────────────────────────
        archetype = analysis.get("analyst_verdict_archetype", "UNKNOWN")
        if isinstance(archetype, list):
            archetype = ", ".join(archetype)
        
        elements.append(Paragraph(f"SENIOR PARTNER VERDICT: {archetype}", self.styles['VerdictHeader']))
        elements.append(Paragraph(str(analysis.get("analyst_verdict_summary", "No summary available.")), self.styles['BodyCopy']))
        elements.append(Spacer(1, 0.2 * inch))

        # ── DIAGNOSIS ─────────────────────────────────────────────────────────
        elements.append(Paragraph("FORENSIC PATTERN DIAGNOSIS", self.styles['SubHeader']))
        
        diag = analysis.get("pattern_diagnosis", "No diagnosis generated.")
        if isinstance(diag, dict):
            diag = diag.get("text", "No diagnosis generated.")
            
        elements.append(Paragraph(str(diag), self.styles['BodyCopy']))
        elements.append(Spacer(1, 0.3 * inch))

        # ── METRICS TABLE ─────────────────────────────────────────────────────
        if isinstance(metrics, dict) and "yearly" in metrics:
            elements.append(Paragraph("5-YEAR FINANCIAL TRAJECTORY", self.styles['SubHeader']))
            table_data = self._build_metrics_table(metrics)
            
            # Dynamic width calculation
            num_cols = len(table_data[0])
            col_widths = [1.5*inch] + [0.9*inch]*(num_cols-1)
            
            t = Table(table_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#64748b")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor("#f1f5f9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.3 * inch))

        # ── FLAGS ─────────────────────────────────────────────────────────────
        flags = analysis.get("flags", [])
        if flags and isinstance(flags, list):
            elements.append(Paragraph("STRUCTURAL RISK & OPPORTUNITY FLAGS", self.styles['SubHeader']))
            for flag in flags:
                if isinstance(flag, dict):
                    name = flag.get('name', 'Alert')
                    emoji = flag.get('emoji', '!')
                    expl = flag.get('explanation', '')
                    flag_text = f"<b>{emoji} {name}</b>: {expl}"
                    elements.append(Paragraph(flag_text, self.styles['BodyCopy']))
                    elements.append(Spacer(1, 0.1 * inch))

        # ── FOOTER ────────────────────────────────────────────────────────────
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("CONFIDENTIAL | FOR INSTITUTIONAL USE ONLY", self.styles['Tagline']))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def _build_metrics_table(self, metrics: dict) -> list:
        """Convert metrics dict into a table format for ReportLab."""
        yearly_data = metrics.get("yearly", [])
        if not yearly_data:
            return [["No Data Available"]]
            
        years = [str(y.get("year", "N/A")) for y in yearly_data]
        header = ["Metric / Year"] + years
        
        rows = [header]
        
        def fmt(val):
            try:
                return f"{float(val):,.0f}" if val is not None else "0"
            except: return "0"

        # Revenue
        rows.append(["Revenue ($M)"] + [fmt(y.get('revenue')) for y in yearly_data])
        rows.append(["EBITDA ($M)"] + [fmt(y.get('ebitda')) for y in yearly_data])
        rows.append(["Net Income ($M)"] + [fmt(y.get('net_income')) for y in yearly_data])
        rows.append(["EBITDA Margin %"] + [f"{y.get('ebitda_margin', 0)}%" for y in yearly_data])
        rows.append(["Net Debt / EBITDA"] + [f"{y.get('leverage', 0)}x" for y in yearly_data])
        rows.append(["Altman Z-Score"] + [f"{y.get('z_score', 0):.2f}" for y in yearly_data])
        rows.append(["ROE %"] + [f"{y.get('roe', 0)}%" for y in yearly_data])
        
        return rows

def generate_financial_pdf(ticker: str, company_name: str, analysis_data: dict) -> io.BytesIO:
    """Convenience wrapper for the report builder."""
    builder = FinancialReportBuilder(ticker, company_name, analysis_data)
    return builder.generate()
