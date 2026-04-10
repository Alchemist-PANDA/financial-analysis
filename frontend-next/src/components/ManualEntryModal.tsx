'use client';

import React, { useState } from 'react';

type YearRow = {
    year: string;
    revenue: number;
    ebitda: number;
    net_income: number;
    ebit: number;
    cash: number;
    debt: number;
    total_assets: number;
    equity: number;
    working_capital: number;
    retained_earnings: number;
    market_value_equity: number;
    accounts_receivable: number;
    inventory: number;
    capex: number;
    cogs: number;
    interest_expense: number;
    current_assets: number;
    current_liabilities: number;
};

type ManualPayload = {
    company: {
        company_name: string;
        sector?: string;
        ticker: string;
    };
    historical_data: YearRow[];
};

type ManualEntryModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: ManualPayload) => void;
};

const DEFAULT_ROWS: YearRow[] = [
    {
        year: '2020',
        revenue: 100,
        ebitda: 20,
        net_income: 10,
        cash: 5,
        debt: 50,
        total_assets: 200,
        equity: 100,
        working_capital: 20,
        retained_earnings: 10,
        ebit: 15,
        market_value_equity: 500,
        accounts_receivable: 10,
        inventory: 5,
        capex: 5,
        cogs: 60,
        interest_expense: 2,
        current_assets: 40,
        current_liabilities: 20,
    },
    {
        year: '2021',
        revenue: 120,
        ebitda: 25,
        net_income: 12,
        cash: 7,
        debt: 45,
        total_assets: 220,
        equity: 110,
        working_capital: 25,
        retained_earnings: 15,
        ebit: 20,
        market_value_equity: 600,
        accounts_receivable: 12,
        inventory: 6,
        capex: 6,
        cogs: 70,
        interest_expense: 2,
        current_assets: 45,
        current_liabilities: 22,
    },
    {
        year: '2022',
        revenue: 150,
        ebitda: 35,
        net_income: 20,
        cash: 15,
        debt: 40,
        total_assets: 250,
        equity: 130,
        working_capital: 40,
        retained_earnings: 25,
        ebit: 30,
        market_value_equity: 800,
        accounts_receivable: 15,
        inventory: 8,
        capex: 8,
        cogs: 80,
        interest_expense: 1,
        current_assets: 60,
        current_liabilities: 25,
    },
    {
        year: '2023',
        revenue: 180,
        ebitda: 45,
        net_income: 25,
        cash: 25,
        debt: 35,
        total_assets: 300,
        equity: 160,
        working_capital: 60,
        retained_earnings: 45,
        ebit: 40,
        market_value_equity: 1200,
        accounts_receivable: 20,
        inventory: 10,
        capex: 10,
        cogs: 90,
        interest_expense: 1,
        current_assets: 80,
        current_liabilities: 30,
    },
    {
        year: '2024',
        revenue: 220,
        ebitda: 60,
        net_income: 35,
        cash: 40,
        debt: 20,
        total_assets: 400,
        equity: 220,
        working_capital: 100,
        retained_earnings: 80,
        ebit: 55,
        market_value_equity: 2000,
        accounts_receivable: 30,
        inventory: 15,
        capex: 12,
        cogs: 100,
        interest_expense: 0,
        current_assets: 120,
        current_liabilities: 35,
    },
];

const EDITABLE_FIELDS: Array<keyof Omit<YearRow, 'year'>> = [
    'revenue',
    'ebitda',
    'net_income',
    'ebit',
    'cash',
    'debt',
    'total_assets',
    'equity',
    'working_capital',
    'retained_earnings',
    'market_value_equity',
    'accounts_receivable',
    'inventory',
    'capex',
    'cogs',
    'interest_expense',
    'current_assets',
    'current_liabilities',
];

const ManualEntryModal = ({ isOpen, onClose, onSubmit }: ManualEntryModalProps) => {
    const [companyName, setCompanyName] = useState('');
    const [sector, setSector] = useState('');
    const [ticker, setTicker] = useState('CUSTOM');
    const [years, setYears] = useState<YearRow[]>(DEFAULT_ROWS);

    if (!isOpen) {
        return null;
    }

    const handleCellChange = (rowIndex: number, field: keyof YearRow, value: string) => {
        setYears((prev) =>
            prev.map((row, index) =>
                index === rowIndex
                    ? { ...row, [field]: field === 'year' ? value : Number(value) || 0 }
                    : row
            )
        );
    };

    const handleLocalSubmit = () => {
        onSubmit({
            company: {
                company_name: companyName.trim() || 'Private Company',
                sector: sector.trim() || 'Unknown',
                ticker: ticker.trim().toUpperCase() || 'CUSTOM',
            },
            historical_data: years,
        });
        onClose();
    };

    return (
        <div className="modal-overlay">
            <div className="modal-container">
                <div className="modal-header">
                    <h3 className="grid-label">MANUAL FORENSIC DATA ENTRY</h3>
                    <button
                        onClick={onClose}
                        style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', fontSize: '20px' }}
                        aria-label="Close manual entry modal"
                    >
                        &times;
                    </button>
                </div>

                <div className="modal-body">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '16px', marginBottom: '24px' }}>
                        <div>
                            <label className="grid-label">COMPANY NAME</label>
                            <input
                                className="modal-input"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="e.g. My Private Venture"
                            />
                        </div>
                        <div>
                            <label className="grid-label">SECTOR</label>
                            <input
                                className="modal-input"
                                value={sector}
                                onChange={(e) => setSector(e.target.value)}
                                placeholder="e.g. Technology"
                            />
                        </div>
                        <div>
                            <label className="grid-label">TICKER</label>
                            <input
                                className="modal-input"
                                value={ticker}
                                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                                placeholder="e.g. CUSTOM"
                            />
                        </div>
                    </div>

                    <div className="table-responsive">
                        <table className="manual-table">
                            <thead>
                                <tr>
                                    <th>METRIC (USD M)</th>
                                    {years.map((row) => (
                                        <th key={row.year}>{row.year}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {EDITABLE_FIELDS.map((field) => (
                                    <tr key={field}>
                                        <td className="metric-name">{field.toUpperCase().replace(/_/g, ' ')}</td>
                                        {years.map((row, rowIndex) => (
                                            <td key={`${field}-${row.year}`}>
                                                <input
                                                    className="table-input"
                                                    type="number"
                                                    value={row[field]}
                                                    onChange={(e) => handleCellChange(rowIndex, field, e.target.value)}
                                                />
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="cancel-btn" onClick={onClose}>CANCEL</button>
                    <button className="submit-btn" onClick={handleLocalSubmit}>RUN FORENSIC ANALYSIS</button>
                </div>
            </div>

            <style jsx>{`
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(15, 23, 42, 0.45);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    padding: 20px;
                }

                .modal-container {
                    background: var(--bg-surface);
                    border: 1px solid var(--border);
                    box-shadow: 0 4px 20px rgba(0,0,0,0.10);
                    max-width: 1020px;
                    width: 100%;
                    max-height: 90vh;
                    display: flex;
                    flex-direction: column;
                }

                .modal-header {
                    padding: 16px 24px;
                    border-bottom: 1px solid var(--border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: var(--bg-elevated);
                }

                .modal-body {
                    padding: 24px;
                    overflow-y: auto;
                }

                .modal-footer {
                    padding: 16px 24px;
                    border-top: 1px solid var(--border);
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                    background: var(--bg-elevated);
                }

                .modal-input {
                    display: block;
                    width: 100%;
                    background: var(--bg-elevated);
                    border: 1px solid var(--border);
                    color: var(--text-primary);
                    padding: 10px;
                    font-size: 13px;
                    margin-top: 8px;
                    outline: none;
                }

                .modal-input:focus {
                    border-color: var(--primary);
                }

                .manual-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 11px;
                }

                .manual-table th {
                    text-align: left;
                    padding: 8px;
                    color: var(--text-muted);
                    background: var(--bg-elevated);
                }

                .manual-table td {
                    padding: 4px;
                    border: 1px solid var(--border);
                }

                .metric-name {
                    color: var(--text-muted);
                    font-weight: bold;
                    width: 190px;
                }

                .table-input {
                    width: 100%;
                    background: transparent;
                    border: none;
                    color: var(--text-primary);
                    text-align: right;
                    padding: 4px;
                    outline: none;
                }

                .table-input:focus {
                    background: rgba(37, 99, 235, 0.10);
                }

                .submit-btn {
                    background: linear-gradient(135deg,#2563EB,#1D4ED8);
                    color: #FFFFFF;
                    border: none;
                    padding: 10px 24px;
                    font-weight: 700;
                    font-size: 12px;
                    cursor: pointer;
                }

                .cancel-btn {
                    background: transparent;
                    border: 1px solid var(--border);
                    color: var(--text-muted);
                    padding: 10px 24px;
                    font-size: 12px;
                    cursor: pointer;
                }

                .table-responsive {
                    overflow-x: auto;
                    border: 1px solid var(--border);
                }

                @media (max-width: 860px) {
                    .modal-body {
                        padding: 16px;
                    }
                }
            `}</style>
        </div>
    );
};

export default ManualEntryModal;
