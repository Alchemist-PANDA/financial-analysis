import React from 'react';

type ViewToggleProps = {
    view: 'simple' | 'expert';
    onChange: (view: 'simple' | 'expert') => void;
};

const ViewToggle = ({ view, onChange }: ViewToggleProps) => {
    return (
        <div className="view-toggle">
            <button className={view === 'simple' ? 'active' : ''} onClick={() => onChange('simple')}>
                Simple View
            </button>
            <button className={view === 'expert' ? 'active' : ''} onClick={() => onChange('expert')}>
                Expert View
            </button>
            <style jsx>{`
                .view-toggle {
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

export default ViewToggle;
