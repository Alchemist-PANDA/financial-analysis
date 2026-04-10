import React from 'react';

type ModeToggleProps = {
    mode: 'credit' | 'investment';
    onChange: (mode: 'credit' | 'investment') => void;
};

const ModeToggle = ({ mode, onChange }: ModeToggleProps) => {
    return (
        <div className="mode-toggle">
            <button
                className={mode === 'credit' ? 'active' : ''}
                onClick={() => onChange('credit')}
            >
                Credit Mode
            </button>
            <button
                className={mode === 'investment' ? 'active' : ''}
                onClick={() => onChange('investment')}
            >
                Investment Mode
            </button>
            <style jsx>{`
                .mode-toggle {
                    display: flex;
                    gap: 8px;
                }
                button {
                    background: transparent;
                    border: 1px solid var(--border-subtle);
                    color: var(--text-secondary);
                    padding: 6px 12px;
                    font-size: 11px;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    cursor: pointer;
                }
                button.active {
                    border-color: var(--border-active);
                    color: var(--text-primary);
                    background: #EFF6FF;
                }
            `}</style>
        </div>
    );
};

export default ModeToggle;
