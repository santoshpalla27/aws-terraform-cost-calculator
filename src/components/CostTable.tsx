import React from 'react';

interface ComponentCost {
    name: string;
    hourly_cost: number;
    monthly_cost: number;
}

interface Resource {
    address: string;
    type: string;
    total_hourly_cost: number;
    total_monthly_cost: number;
    cost_components: any[];
}

interface Props {
    resources: Resource[];
    currency: string;
}

const CostTable: React.FC<Props> = ({ resources, currency }) => {
    return (
        <div className="card" style={{ marginTop: '2rem', overflowX: 'auto' }}>
            <h3>Resource Breakdown</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', marginTop: '1rem' }}>
                <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                        <th style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Resource</th>
                        <th style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Type</th>
                        <th style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Hourly ({currency})</th>
                        <th style={{ padding: '1rem', color: 'var(--text-secondary)' }}>Monthly ({currency})</th>
                    </tr>
                </thead>
                <tbody>
                    {resources.map((res) => (
                        <tr key={res.address} style={{ borderBottom: '1px solid var(--border)' }}>
                            <td style={{ padding: '1rem' }}>{res.address}</td>
                            <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>{res.type}</td>
                            <td style={{ padding: '1rem' }}>{res.total_hourly_cost.toFixed(4)}</td>
                            <td style={{ padding: '1rem' }}>{res.total_monthly_cost.toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default CostTable;
