'use client';
import React, { useState } from 'react';

const ManualEntryModal = ({ isOpen, onClose, onSubmit }: { isOpen: boolean, onClose: () => void, onSubmit: (data: any) => void }) => {
    const [companyName, setCompanyName] = useState('');
    const [sector, setSector] = useState('');
    const [years, setYears] = useState([
        { year: '2020', revenue: 100, ebitda: 20, net_income: 10, cash: 5, debt: 50, total_assets: 200, equity: 100, working_capital: 20, retained_earnings: 10, ebit: 15, market_value_equity: 500, accounts_receivable: 10, inventory: 5, capex: 5 },
        { year: '2021', revenue: 120, ebitda: 25, net_income: 12, cash: 7, debt: 45, total_assets: 220, equity: 110, working_capital: 25, retained_earnings: 15, ebit: 20, market_value_equity: 600, accounts_receivable: 12, inventory: 6, capex: 6 },
        { year: '2022', revenue: 150, ebitda: 35, net_income: 20, cash: 15, debt: 40, total_assets: 250, equity: 130, working_capital: 40, retained_earnings: 25, ebit: 30, market_value_equity: 800, accounts_receivable: 15, inventory: 8, capex: 8 },
        { year: '2023', revenue: 180, ebitda: 45, net_income: 25, cash: 25, debt: 35, total_assets: 300, equity: 160, working_capital: 60, retained_earnings: 45, ebit: 40, market_value_equity: 1200, accounts_receivable: 20, inventory: 10, capex: 10 },
        { year: '2024', revenue: 220, ebitda: 60, net_income: 35, cash: 40, debt: 20, total_assets: 400, equity: 220, working_capital: 100, retained_earnings: 80, ebit: 55, market_value_equity: 2000, accounts_receivable: 30, inventory: 15, capex: 12 },
    ]);

    if (!isOpen) return null;

    const handleCellChange = (index: number, field: string, value: string) => {
        const newYears = [...years];
        (newYears[index] as any)[field] = parseFloat(value) || 0;
        setYears(newYears);
    };

    const handleLocalSubmit = () => {
        onSubmit({
            company: { company_name: companyName, sector, ticker: "CUSTOM" },
            historical_data: years
        });
        onClose();
    };

    return (
        <div className="modal-overlay">
            <div className="modal-container">
                <div className="modal-header">
                    <h3 className="grid-label">MANUAL FORENSIC DATA ENTRY</h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '20px' }}>&times;</button>
                </div>
                
                <div className="modal-body">
                    <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
                        <div style={{ flex: 1 }}>
                            <label className="grid-label">COMPANY NAME</label>
                            <input className="modal-input" value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder="e.g. My Private Venture" />
                        </div>
                        <div style={{ flex: 1 }}>
                            <label className="grid-label">SECTOR</label>
                            <input className="modal-input" value={sector} onChange={e => setSector(e.target.value)} placeholder="e.g. Technology" />
                        </div>
                    </div>

                    <div className="table-responsive">
                    <table className="manual-table">
                        <thead>
                            <tr>
                                <th>METRIC (USD M)</th>
                                {years.map(y => <th key={y.year}>{y.year}</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            {['revenue', 'ebitda', 'net_income', 'ebit', 'cash', 'debt', 'total_assets', 'equity', 'working_capital', 'retained_earnings', 'market_value_equity', 'accounts_receivable', 'inventory', 'capex'].map(field => (
                                <tr key={field}>
                                    <td className="metric-name">{field.toUpperCase().replace(/_/g, ' ')}</td>
                                    {years.map((y, i) => (
                                        <td key={i}>
                                            <input 
                                                className="table-input"
                                                type="number"
                                                value={(y as any)[field]}
                                                onChange={(e) => handleCellChange(i, field, e.target.value)}
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
                    grid: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    padding: 20px;
                }
                .modal-container {
                    background: #050505;
                    border: 1px solid var(--border);
                    max-width: 900px;
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
                    background: #111;
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
                    background: #111;
                }
                .modal-input {
                    display: block;
                    width: 100%;
                    background: #000;
                    border: 1px solid var(--border);
                    color: var(--foreground);
                    padding: 10px;
                    font-size: 13px;
                    margin-top: 8px;
                    outline: none;
                }
                .modal-input:focus { border-color: var(--primary); }
                
                .manual-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 11px;
                }
                .manual-table th {
                    text-align: left;
                    padding: 8px;
                    color: var(--text-muted);
                    background: #111;
                }
                .manual-table td {
                    padding: 4px;
                    border: 1px solid #111;
                }
                .metric-name {
                    color: var(--text-muted);
                    font-weight: bold;
                    width: 160px;
                }
                .table-input {
                    width: 100%;
                    background: transparent;
                    border: none;
                    color: var(--primary);
                    text-align: right;
                    padding: 4px;
                    outline: none;
                }
                .table-input:focus { background: rgba(14, 165, 233, 0.1); }
                
                .submit-btn {
                    background: var(--primary);
                    color: #000;
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
            `}</style>
        </div>
    );
};

export default ManualEntryModal;
